import { useRef, useState } from 'react';
import { isAxiosError } from 'axios';
import { useParams, useRevalidator } from 'react-router';
import {
  ArrowUpTrayIcon,
  DocumentTextIcon,
  ExclamationCircleIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline';

import { Button, OutlineButton } from '../../../../../../Buttons';
import Modal from '../../../../../../Modal';
import { getDataProductName } from '../DataProductsTable';
import { formatFileSize, parseXml, XML_FILE_MAX_SIZE } from './xmlUtils';

import { DataProduct } from '../../../Project';

import api from '../../../../../../../api';

export default function XmlMetadataAttachModal({
  dataProduct,
  open,
  setOpen,
}: {
  dataProduct: DataProduct;
  open: boolean;
  setOpen: React.Dispatch<React.SetStateAction<boolean>>;
}) {
  const [error, setError] = useState<string | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [stagedFile, setStagedFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const params = useParams();
  const revalidator = useRevalidator();

  function reset() {
    setError(null);
    setIsDragOver(false);
    setIsUploading(false);
    setStagedFile(null);
  }

  function handleClose() {
    reset();
    setOpen(false);
  }

  async function stageFile(file: File) {
    setError(null);
    setStagedFile(null);
    if (!file.name.toLowerCase().endsWith('.xml')) {
      setError(`Couldn't read "${file.name}" — that file isn't valid XML.`);
      return;
    }
    if (file.size > XML_FILE_MAX_SIZE) {
      setError(`"${file.name}" is too large (max 10 MB).`);
      return;
    }
    const parsed = parseXml(await file.text());
    if ('error' in parsed) {
      setError(`Couldn't read "${file.name}" — that file isn't valid XML.`);
      return;
    }
    setStagedFile(file);
  }

  async function handleAttach() {
    if (!stagedFile) return;
    setIsUploading(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append('file', stagedFile);
      const response = await api.post(
        `projects/${params.projectId}/flights/${params.flightId}/data_products/${dataProduct.id}/xml`,
        formData,
        { headers: { 'Content-Type': 'multipart/form-data' } }
      );
      if (response) {
        handleClose();
        revalidator.revalidate();
      } else {
        setError('Unable to attach XML file');
      }
    } catch (err) {
      if (isAxiosError(err) && err.response?.data?.detail) {
        setError(err.response.data.detail);
      } else {
        setError('Unable to attach XML file');
      }
    } finally {
      setIsUploading(false);
    }
  }

  return (
    <Modal open={open} setOpen={setOpen}>
      <div className="bg-white px-4 pb-4 pt-5 sm:p-6 sm:pb-4">
        <h3 className="text-lg font-medium leading-6 text-gray-900">
          Attach XML metadata
        </h3>
        <p className="mt-1 text-sm text-gray-500">
          Associate a supplemental XML file with{' '}
          <span className="font-semibold">
            {getDataProductName(dataProduct.data_type)}
          </span>
          .
        </p>
        <div
          className={`mt-4 flex flex-col items-center justify-center gap-2 border-2 border-dashed rounded-xl p-8 text-center ${
            isDragOver
              ? 'border-sky-600 bg-sky-50'
              : 'border-slate-300 bg-slate-50'
          }`}
          onDragOver={(e) => {
            e.preventDefault();
            setIsDragOver(true);
          }}
          onDragLeave={() => setIsDragOver(false)}
          onDrop={(e) => {
            e.preventDefault();
            setIsDragOver(false);
            if (e.dataTransfer.files.length > 0) {
              stageFile(e.dataTransfer.files[0]);
            }
          }}
        >
          <div className="rounded-lg bg-sky-100 p-2">
            <ArrowUpTrayIcon className="w-6 h-6 text-sky-600" />
          </div>
          <p className="text-sm font-semibold text-slate-700">
            Drag &amp; drop an XML file
          </p>
          <p className="text-sm text-slate-500">
            or{' '}
            <button
              type="button"
              className="font-semibold text-sky-600 hover:text-sky-700"
              onClick={() => fileInputRef.current?.click()}
            >
              browse your computer
            </button>
          </p>
          <p className="text-xs text-slate-400">.xml only · up to 10 MB</p>
          <input
            ref={fileInputRef}
            type="file"
            accept=".xml,text/xml,application/xml"
            className="hidden"
            onChange={(e) => {
              if (e.target.files && e.target.files.length > 0) {
                stageFile(e.target.files[0]);
              }
              e.target.value = '';
            }}
          />
        </div>
        {stagedFile && (
          <div className="mt-3 flex items-center justify-between gap-2 bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-2">
            <div className="flex items-center gap-2 min-w-0">
              <DocumentTextIcon className="w-5 h-5 shrink-0 text-sky-600" />
              <div className="min-w-0 text-left">
                <div
                  className="text-sm font-semibold text-slate-700 truncate"
                  title={stagedFile.name}
                >
                  {stagedFile.name}
                </div>
                <div className="text-[11px] font-semibold text-slate-500">
                  {formatFileSize(stagedFile.size)}
                </div>
              </div>
            </div>
            <button
              type="button"
              aria-label="Remove staged file"
              className="shrink-0 text-slate-500 hover:text-red-500"
              onClick={() => setStagedFile(null)}
            >
              <XMarkIcon className="w-4 h-4" />
            </button>
          </div>
        )}
        {error && (
          <div className="mt-3 flex items-center gap-2 text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
            <ExclamationCircleIcon className="w-5 h-5 shrink-0" />
            <span>{error}</span>
          </div>
        )}
      </div>
      <div className="flex items-center justify-between gap-4 bg-gray-50 px-4 py-3 sm:px-6">
        <div className="w-36">
          <OutlineButton type="button" size="sm" onClick={handleClose}>
            Cancel
          </OutlineButton>
        </div>
        <div className="w-36">
          <Button
            type="button"
            size="sm"
            disabled={!stagedFile || isUploading}
            onClick={handleAttach}
          >
            {isUploading ? 'Attaching...' : 'Attach file'}
          </Button>
        </div>
      </div>
    </Modal>
  );
}
