import { useState } from 'react';
import { ClipboardIcon } from '@heroicons/react/24/outline';

// matches a full tag-like chunk on a single line
const TAG_CHUNK_REGEX = /<[^>]*>/g;
// matches attribute name="value" pairs inside a tag chunk
const ATTRIBUTE_REGEX = /([\w:.-]+)(=)("[^"]*")/g;
// matches the tag name following the opening punctuation
const TAG_NAME_REGEX = /^(<\/?)([\w:.-]+)/;

function highlightTagChunk(chunk: string, key: number): React.ReactNode {
  // declarations (<?xml ?>) and comments/doctypes (<!) render muted
  if (chunk.startsWith('<?') || chunk.startsWith('<!')) {
    return (
      <span key={key} className="text-[#98a3b3]">
        {chunk}
      </span>
    );
  }

  const nodes: React.ReactNode[] = [];
  let rest = chunk;
  const tagNameMatch = rest.match(TAG_NAME_REGEX);
  if (tagNameMatch) {
    nodes.push(
      <span key={`${key}-open`} className="text-[#8a98ad]">
        {tagNameMatch[1]}
      </span>,
      <span key={`${key}-tag`} className="text-[#1f74bf]">
        {tagNameMatch[2]}
      </span>
    );
    rest = rest.slice(tagNameMatch[0].length);
  }

  let lastIndex = 0;
  let attrIndex = 0;
  for (const match of rest.matchAll(ATTRIBUTE_REGEX)) {
    if (match.index > lastIndex) {
      nodes.push(rest.slice(lastIndex, match.index));
    }
    nodes.push(
      <span key={`${key}-attr-${attrIndex}`}>
        <span className="text-[#b06a1e]">{match[1]}</span>
        <span className="text-[#8a98ad]">{match[2]}</span>
        <span className="text-[#2f8f5b]">{match[3]}</span>
      </span>
    );
    lastIndex = match.index + match[0].length;
    attrIndex += 1;
  }
  if (lastIndex < rest.length) {
    nodes.push(
      <span key={`${key}-close`} className="text-[#8a98ad]">
        {rest.slice(lastIndex)}
      </span>
    );
  }

  return <span key={key}>{nodes}</span>;
}

function highlightLine(line: string): React.ReactNode[] {
  const nodes: React.ReactNode[] = [];
  let lastIndex = 0;
  let chunkIndex = 0;
  for (const match of line.matchAll(TAG_CHUNK_REGEX)) {
    if (match.index > lastIndex) {
      nodes.push(
        <span key={`text-${chunkIndex}`} className="text-[#33404f]">
          {line.slice(lastIndex, match.index)}
        </span>
      );
    }
    nodes.push(highlightTagChunk(match[0], chunkIndex));
    lastIndex = match.index + match[0].length;
    chunkIndex += 1;
  }
  if (lastIndex < line.length) {
    nodes.push(
      <span key={`text-${chunkIndex}`} className="text-[#33404f]">
        {line.slice(lastIndex)}
      </span>
    );
  }
  return nodes;
}

export default function XmlRawView({ content }: { content: string }) {
  const [isCopied, setIsCopied] = useState(false);
  const lines = content.split('\n');

  return (
    <div className="relative rounded-[10px] border border-slate-200 bg-slate-50/50 overflow-hidden">
      <button
        type="button"
        className="absolute top-2 right-2 flex items-center gap-1 rounded-md border border-slate-300 bg-white px-2 py-1 text-xs font-semibold text-slate-600 hover:text-sky-600"
        onClick={() => {
          navigator.clipboard.writeText(content);
          setIsCopied(true);
          setTimeout(() => {
            setIsCopied(false);
          }, 3000);
        }}
      >
        <ClipboardIcon className="w-3.5 h-3.5" />
        {isCopied ? 'Copied' : 'Copy'}
      </button>
      <div className="flex overflow-x-auto">
        <div className="shrink-0 select-none bg-slate-100 px-2 py-3 text-right font-mono text-[13px] leading-relaxed text-slate-400">
          {lines.map((_, index) => (
            <div key={index}>{index + 1}</div>
          ))}
        </div>
        <pre className="flex-1 px-3 py-3 font-mono text-[13px] leading-relaxed">
          {lines.map((line, index) => (
            <div key={index} className="whitespace-pre">
              {highlightLine(line)}
            </div>
          ))}
        </pre>
      </div>
    </div>
  );
}
