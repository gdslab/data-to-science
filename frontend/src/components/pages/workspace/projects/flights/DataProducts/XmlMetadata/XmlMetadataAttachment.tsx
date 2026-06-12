import { useState } from 'react';
import { useParams, useRevalidator } from 'react-router';
import {
  ArrowDownTrayIcon,
  DocumentTextIcon,
  EyeIcon,
  PlusIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline';

import { AlertBar, Status } from '../../../../../../Alert';
import { ConfirmationPopup } from '../../../../../../ConfirmationPopup';
import Modal from '../../../../../../Modal';
import { isGeoTIFF } from '../DataProductsTable';
import XmlMetadataAttachModal from './XmlMetadataAttachModal';
import XmlMetadataViewerModal from './XmlMetadataViewerModal';
import { downloadXml, formatFileSize } from './xmlUtils';
import { useProjectContext } from '../../../ProjectContext';

import { DataProduct } from '../../../Project';

import api from '../../../../../../../api';

export default function XmlMetadataAttachment({
  dataProduct,
  compact = false,
  variant = 'pill',
}: {
  dataProduct: DataProduct;
  compact?: boolean;
  variant?: 'pill' | 'icon';
}) {
  const [openAttachModal, setOpenAttachModal] = useState(false);
  const [openRemoveConfirmation, setOpenRemoveConfirmation] = useState(false);
  const [openViewerModal, setOpenViewerModal] = useState(false);
  const [status, setStatus] = useState<Status | null>(null);
  const params = useParams();
  const revalidator = useRevalidator();
  const { projectRole } = useProjectContext();

  const canEdit = projectRole === 'owner' || projectRole === 'manager';
  // xml metadata limited to raster and point cloud data products
  const supportsXml =
    isGeoTIFF(dataProduct.data_type) ||
    dataProduct.data_type === 'point_cloud';
  const xmlMetadata = dataProduct.xml_metadata;

  if (!xmlMetadata && (!canEdit || !supportsXml)) {
    return null;
  }

  return (
    <div className={variant === 'icon' ? '' : compact ? 'w-56' : 'w-full'}>
      {variant === 'icon' ? (
        xmlMetadata ? (
          <button
            type="button"
            aria-label="View XML metadata"
            title="View XML metadata"
            className="h-5 flex items-center text-xs font-bold hover:scale-110"
            onClick={() => setOpenViewerModal(true)}
          >
            XML
          </button>
        ) : (
          <button
            type="button"
            aria-label="Attach XML metadata"
            title="Attach XML metadata"
            className="h-5 flex items-center text-xs font-bold hover:scale-110"
            onClick={() => setOpenAttachModal(true)}
          >
            + XML
          </button>
        )
      ) : xmlMetadata ? (
        <div
          className={`flex items-center justify-between gap-2 bg-slate-50 border border-slate-200 rounded-lg px-2.5 ${
            compact ? 'py-1.5' : 'py-2'
          }`}
        >
          <div
            className="flex items-center gap-2 min-w-0 cursor-pointer"
            onClick={() => setOpenViewerModal(true)}
          >
            <DocumentTextIcon className="w-5 h-5 shrink-0 text-sky-600" />
            <div className="min-w-0 text-left">
              <div
                className="text-sm font-semibold text-slate-700 truncate"
                title={xmlMetadata.original_filename}
              >
                {xmlMetadata.original_filename}
              </div>
              {!compact && (
                <div className="text-[11px] font-semibold text-slate-500">
                  {formatFileSize(xmlMetadata.file_size)}
                </div>
              )}
            </div>
          </div>
          <div className="flex items-center gap-1.5 shrink-0">
            <button
              type="button"
              aria-label="View XML metadata"
              title="View XML metadata"
              className="text-slate-500 hover:text-sky-600"
              onClick={() => setOpenViewerModal(true)}
            >
              <EyeIcon className="w-4 h-4" />
            </button>
            <button
              type="button"
              aria-label="Download XML metadata"
              title="Download XML metadata"
              className="text-slate-500 hover:text-sky-600"
              onClick={() =>
                downloadXml(xmlMetadata.original_filename, xmlMetadata.content)
              }
            >
              <ArrowDownTrayIcon className="w-4 h-4" />
            </button>
            {canEdit && (
              <button
                type="button"
                aria-label="Remove XML metadata"
                title="Remove XML metadata"
                className="text-slate-500 hover:text-red-500"
                onClick={() => setOpenRemoveConfirmation(true)}
              >
                <XMarkIcon className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      ) : (
        <button
          type="button"
          className="w-full flex items-center justify-center gap-1 text-sm font-semibold text-slate-500 border border-dashed border-slate-300 rounded-lg px-3 py-1.5 hover:text-sky-600 hover:border-sky-600"
          onClick={() => setOpenAttachModal(true)}
        >
          <PlusIcon className="w-4 h-4" />
          Attach XML metadata
        </button>
      )}
      {supportsXml && (
        <XmlMetadataAttachModal
          dataProduct={dataProduct}
          open={openAttachModal}
          setOpen={setOpenAttachModal}
        />
      )}
      {xmlMetadata && (
        <XmlMetadataViewerModal
          dataProduct={dataProduct}
          xmlMetadata={xmlMetadata}
          open={openViewerModal}
          setOpen={setOpenViewerModal}
          onRemove={
            canEdit
              ? () => {
                  setOpenViewerModal(false);
                  setOpenRemoveConfirmation(true);
                }
              : undefined
          }
        />
      )}
      <Modal open={openRemoveConfirmation} setOpen={setOpenRemoveConfirmation}>
        <ConfirmationPopup
          title="Are you sure you want to remove this XML file?"
          content="The XML file will be permanently removed from the data product. You can attach a new XML file afterward."
          confirmText="Yes, remove"
          rejectText="No, keep XML file"
          setOpen={setOpenRemoveConfirmation}
          onConfirm={async () => {
            setStatus(null);
            try {
              const response = await api.delete(
                `projects/${params.projectId}/flights/${params.flightId}/data_products/${dataProduct.id}/xml`
              );
              if (response) {
                setOpenRemoveConfirmation(false);
                revalidator.revalidate();
              } else {
                setOpenRemoveConfirmation(false);
                setStatus({
                  type: 'error',
                  msg: 'Unable to remove XML file',
                });
              }
            } catch {
              setOpenRemoveConfirmation(false);
              setStatus({
                type: 'error',
                msg: 'Unable to remove XML file',
              });
            }
          }}
        />
      </Modal>
      {status ? (
        <AlertBar alertType={status.type}>{status.msg}</AlertBar>
      ) : null}
    </div>
  );
}
