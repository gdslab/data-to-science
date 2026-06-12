import { useEffect, useMemo, useState } from 'react';
import {
  ArrowDownTrayIcon,
  DocumentTextIcon,
  TrashIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline';

import Modal from '../../../../../../Modal';
import { getDataProductName } from '../DataProductsTable';
import XmlRawView from './XmlRawView';
import XmlTree, { collectCollapsiblePaths } from './XmlTree';
import { downloadXml, formatFileSize, parseXml, XmlNode } from './xmlUtils';

import { DataProduct, XmlMetadata } from '../../../Project';

type ViewerMode = 'structure' | 'raw';

function getDefaultExpandedPaths(root: XmlNode): Set<string> {
  // expand root and its immediate children; collapse deeper levels
  const paths = new Set<string>(['0']);
  root.children.forEach((_, index) => paths.add(`0.${index}`));
  return paths;
}

export default function XmlMetadataViewerModal({
  dataProduct,
  xmlMetadata,
  open,
  setOpen,
  onRemove,
}: {
  dataProduct: DataProduct;
  xmlMetadata: XmlMetadata;
  open: boolean;
  setOpen: React.Dispatch<React.SetStateAction<boolean>>;
  onRemove?: () => void;
}) {
  const [expandedPaths, setExpandedPaths] = useState<Set<string>>(new Set());
  const [mode, setMode] = useState<ViewerMode>('structure');

  const parsed = useMemo(
    () => (open ? parseXml(xmlMetadata.content) : null),
    [open, xmlMetadata.content]
  );
  const root = parsed && 'root' in parsed ? parsed.root : null;
  const allExpanded = root
    ? collectCollapsiblePaths(root).every((path) => expandedPaths.has(path))
    : false;

  useEffect(() => {
    if (root) {
      setExpandedPaths(getDefaultExpandedPaths(root));
    }
  }, [root]);

  function handleToggle(path: string) {
    setExpandedPaths((previous) => {
      const next = new Set(previous);
      if (next.has(path)) {
        next.delete(path);
      } else {
        next.add(path);
      }
      return next;
    });
  }

  return (
    <Modal open={open} setOpen={setOpen}>
      {/* header */}
      <div className="flex items-center justify-between gap-4 border-b border-slate-200 px-4 py-4 sm:px-6">
        <div className="flex items-center gap-3 min-w-0">
          <div className="shrink-0 rounded-lg bg-sky-100 p-2">
            <DocumentTextIcon className="w-6 h-6 text-sky-600" />
          </div>
          <div className="min-w-0 text-left">
            <h3
              className="text-lg font-bold text-gray-900 truncate"
              title={xmlMetadata.original_filename}
            >
              {xmlMetadata.original_filename}
            </h3>
            <p className="text-[13px] font-semibold text-slate-500 truncate">
              {formatFileSize(xmlMetadata.file_size)} ·{' '}
              {getDataProductName(dataProduct.data_type)}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <button
            type="button"
            className="flex items-center gap-1.5 rounded-lg bg-accent3 px-3 py-1.5 text-sm font-semibold text-white hover:bg-accent3-dark"
            onClick={() =>
              downloadXml(xmlMetadata.original_filename, xmlMetadata.content)
            }
          >
            <ArrowDownTrayIcon className="w-4 h-4" />
            Download
          </button>
          {onRemove && (
            <button
              type="button"
              className="flex items-center gap-1.5 rounded-lg border border-slate-300 px-3 py-1.5 text-sm font-semibold text-slate-600 hover:border-red-300 hover:text-red-600"
              onClick={onRemove}
            >
              <TrashIcon className="w-4 h-4" />
              Remove
            </button>
          )}
          <button
            type="button"
            aria-label="Close"
            className="rounded-lg border border-slate-300 p-1.5 text-slate-500 hover:text-slate-700"
            onClick={() => setOpen(false)}
          >
            <XMarkIcon className="w-4 h-4" />
          </button>
        </div>
      </div>
      {/* toolbar */}
      <div className="flex items-center justify-between gap-4 border-b border-slate-200 px-4 py-2.5 sm:px-6">
        <div className="flex rounded-lg bg-slate-200 p-0.5">
          {(['structure', 'raw'] as ViewerMode[]).map((viewerMode) => (
            <button
              key={viewerMode}
              type="button"
              className={`rounded-md px-3 py-1 text-sm font-semibold capitalize ${
                mode === viewerMode
                  ? 'bg-white text-slate-700 shadow-sm'
                  : 'text-slate-500 hover:text-slate-700'
              }`}
              onClick={() => setMode(viewerMode)}
            >
              {viewerMode}
            </button>
          ))}
        </div>
        {mode === 'structure' && root && (
          <button
            type="button"
            className="text-sm font-semibold text-sky-600 hover:text-sky-700"
            onClick={() => {
              if (allExpanded) {
                setExpandedPaths(new Set());
              } else {
                setExpandedPaths(new Set(collectCollapsiblePaths(root)));
              }
            }}
          >
            {allExpanded ? 'Collapse all' : 'Expand all'}
          </button>
        )}
      </div>
      {/* content (swappable region; future Summary tab slots in here) */}
      <div className="max-h-[60vh] overflow-auto bg-white px-4 py-4 sm:px-6">
        {mode === 'structure' && root ? (
          <XmlTree
            root={root}
            expandedPaths={expandedPaths}
            onToggle={handleToggle}
          />
        ) : (
          <XmlRawView content={xmlMetadata.content} />
        )}
      </div>
    </Modal>
  );
}
