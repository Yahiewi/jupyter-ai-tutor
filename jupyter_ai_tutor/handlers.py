import json

import tornado
from jupyter_server.base.handlers import APIHandler
from tornado.iostream import StreamClosedError


class ExplainHandler(APIHandler):
    @tornado.web.authenticated
    async def post(self):
        body = self.get_json_body()
        if not body:
            raise tornado.web.HTTPError(400, "Missing request body")

        message_body = body.get("body", "")
        description = body.get("description", "")
        reference_solution = body.get("reference_solution", "")
        evaluation_criteria = body.get("evaluation_criteria", "")

        formatted_message = ""
        if description:
            formatted_message += f"<exercise_description>\n{description}\n</exercise_description>\n\n"

        formatted_message += f"{message_body}"

        if reference_solution:
            formatted_message += f"\n\n<reference_solution>\n{reference_solution}\n</reference_solution>"
        if evaluation_criteria:
            formatted_message += f"\n\n<evaluation_criteria>\n{evaluation_criteria}\n</evaluation_criteria>"

        message_body = formatted_message.strip()

        config_manager = self.settings.get("jupyternaut.config_manager")
        if not config_manager:
            raise tornado.web.HTTPError(
                503, "Jupyternaut config manager is not available"
            )
        if not config_manager.chat_model:
            raise tornado.web.HTTPError(
                503,
                "No chat model is configured. Set one in 'Settings > AI Settings'.",
            )

        self.set_header("Content-Type", "text/event-stream")
        self.set_header("Cache-Control", "no-cache")
        self.set_header("X-Accel-Buffering", "no")

        system_prompt = self.settings.get("jupyter_ai_tutor.system_prompt", "")

        try:
            from jupyter_ai_jupyternaut.jupyternaut.chat_models import ChatLiteLLM
            from langchain_core.messages import HumanMessage, SystemMessage

            model = ChatLiteLLM(
                **config_manager.chat_model_args,
                model=config_manager.chat_model,
                streaming=True,
            )

            async for chunk in model.astream(
                [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=message_body),
                ]
            ):
                text = (
                    chunk.content
                    if isinstance(chunk.content, str)
                    else "".join(
                        block.get("text", "")
                        for block in chunk.content
                        if isinstance(block, dict)
                    )
                )
                if text:
                    self.write(f"data: {json.dumps({'text': text})}\n\n")
                    self.flush()

        except StreamClosedError:
            return  # Client disconnected; stop streaming
        except Exception as e:
            self.log.exception("Error during tutor LLM call")
            try:
                self.write(f"data: {json.dumps({'error': str(e)})}\n\n")
                self.flush()
            except StreamClosedError:
                return

        try:
            self.write("data: [DONE]\n\n")
            self.flush()
            self.finish()
        except StreamClosedError:
            pass
