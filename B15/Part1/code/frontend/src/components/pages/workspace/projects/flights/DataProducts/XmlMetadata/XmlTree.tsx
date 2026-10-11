import { ChevronDownIcon, ChevronRightIcon } from '@heroicons/react/24/outline';

import { XmlNode } from './xmlUtils';

export function collectCollapsiblePaths(
  node: XmlNode,
  path = '0',
  acc: string[] = []
): string[] {
  if (node.children.length > 0) {
    acc.push(path);
    node.children.forEach((child, index) =>
      collectCollapsiblePaths(child, `${path}.${index}`, acc)
    );
  }
  return acc;
}

function XmlTreeNode({
  node,
  path,
  expandedPaths,
  onToggle,
}: {
  node: XmlNode;
  path: string;
  expandedPaths: Set<string>;
  onToggle: (path: string) => void;
}) {
  const hasChildren = node.children.length > 0;
  const isExpanded = expandedPaths.has(path);

  return (
    <div className="font-mono text-[13px] leading-relaxed">
      <div className="flex items-center gap-1.5 min-w-0">
        {hasChildren ? (
          <button
            type="button"
            aria-label={isExpanded ? 'Collapse node' : 'Expand node'}
            className="shrink-0 text-slate-400 hover:text-slate-600"
            onClick={() => onToggle(path)}
          >
            {isExpanded ? (
              <ChevronDownIcon className="w-3.5 h-3.5" />
            ) : (
              <ChevronRightIcon className="w-3.5 h-3.5" />
            )}
          </button>
        ) : (
          <span className="w-3.5 shrink-0" />
        )}
        <span className="font-bold text-[#1f74bf] shrink-0">{node.tag}</span>
        {Object.entries(node.attrs).map(([name, value]) => (
          <span
            key={name}
            className="shrink-0 rounded border border-[#f0e0c8] bg-[#fff5e9] px-1.5 text-[11.5px] text-[#b06a1e]"
            title={`${name}="${value}"`}
          >
            {name}=<span className="text-[#2f8f5b]">"{value}"</span>
          </span>
        ))}
        {!hasChildren && node.text && (
          <span className="text-slate-700 truncate" title={node.text}>
            : {node.text}
          </span>
        )}
        {hasChildren && (
          <span className="shrink-0 rounded-full bg-slate-100 px-1.5 text-[11px] text-slate-500">
            {node.children.length}
          </span>
        )}
      </div>
      {hasChildren && isExpanded && (
        <div className="ml-[18px] border-l border-slate-100 pl-2">
          {node.children.map((child, index) => (
            <XmlTreeNode
              key={`${path}.${index}`}
              node={child}
              path={`${path}.${index}`}
              expandedPaths={expandedPaths}
              onToggle={onToggle}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export default function XmlTree({
  root,
  expandedPaths,
  onToggle,
}: {
  root: XmlNode;
  expandedPaths: Set<string>;
  onToggle: (path: string) => void;
}) {
  return (
    <XmlTreeNode
      node={root}
      path="0"
      expandedPaths={expandedPaths}
      onToggle={onToggle}
    />
  );
}
