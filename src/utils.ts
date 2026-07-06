export function isContinuous(numbers: number[]): boolean {
  if (numbers.length <= 1) {
    return true;
  }

  for (let i = 1; i < numbers.length; i++) {
    if (numbers[i] !== numbers[i - 1] + 1) {
      return false;
    }
  }

  return true;
}

export interface ICriteriaItem {
  label?: string;
  title?: string;
  name?: string;
  description?: string;
  desc?: string;
}

/**
 * Decodes a ROT13 encoded string.
 */
export function decodeRot13(str: string): string {
  return str.replace(/[a-zA-Z]/g, c => {
    const base = c <= 'Z' ? 65 : 97;
    return String.fromCharCode(((c.charCodeAt(0) - base + 13) % 26) + base);
  });
}

export function formatEvaluationCriteria(criteriaData: unknown): string {
  if (!criteriaData) {
    return '';
  }
  if (typeof criteriaData === 'string') {
    return criteriaData;
  }

  const data = criteriaData as { criteria?: ICriteriaItem[] } | ICriteriaItem[];
  const list = Array.isArray(data) ? data : data.criteria || [];

  return list
    .map(item => {
      if (item && typeof item === 'object') {
        const label = item.label || item.title || item.name || '';
        const desc = item.description || item.desc || '';
        return label && desc ? `- ${label}: ${desc}` : `- ${label || desc}`;
      }
      return typeof item === 'string' ? `- ${item}` : '';
    })
    .filter(Boolean)
    .join('\n');
}
