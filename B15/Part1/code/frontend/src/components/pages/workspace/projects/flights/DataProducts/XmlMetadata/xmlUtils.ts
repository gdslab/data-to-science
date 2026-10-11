export type XmlNode = {
  tag: string;
  attrs: Record<string, string>;
  text?: string; // direct text content if this node has no element children
  children: XmlNode[];
};

export type ParsedXml =
  | { root: XmlNode; lineCount: number }
  | { error: string };

export const XML_FILE_MAX_SIZE = 10 * 1024 * 1024; // 10 MB (matches backend cap)

export function parseXml(raw: string): ParsedXml {
  const doc = new DOMParser().parseFromString(raw, 'application/xml');
  if (doc.querySelector('parsererror')) return { error: 'Not valid XML' };
  const toNode = (el: Element): XmlNode => {
    const children = Array.from(el.children).map(toNode);
    return {
      tag: el.tagName,
      attrs: Object.fromEntries(
        Array.from(el.attributes).map((a) => [a.name, a.value])
      ),
      text: children.length ? undefined : el.textContent?.trim() || undefined,
      children,
    };
  };
  return { root: toNode(doc.documentElement), lineCount: raw.split('\n').length };
}

export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function downloadXml(filename: string, content: string): void {
  const blob = new Blob([content], { type: 'application/xml' });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  URL.revokeObjectURL(url);
}
