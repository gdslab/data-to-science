import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronDownIcon } from '@heroicons/react/24/outline';

import Alert, { Status } from '../../Alert';
import {
  Button,
  CopyShortURLButton,
  CopyURLButton,
  DownloadQRButton,
} from '../../Buttons';
import { DataProduct } from '../../pages/projects/Project';
import { useMapContext } from '../MapContext';
import { Project } from '../../pages/projects/ProjectList';
import {
  MultibandSymbology,
  SingleBandSymbology,
} from '../RasterSymbologyContext';

import api from '../../../api';
import { createAndClickDownloadLink } from '../../pages/projects/mapLayers/utils';

export default function RasterSymbologyAccessControls({
  dataProduct,
  project,
  symbology,
  refreshUrl,
}: {
  dataProduct: DataProduct;
  project: Project;
  symbology?: SingleBandSymbology | MultibandSymbology;
  refreshUrl?: string;
}) {
  const [accessOption, setAccessOption] = useState<boolean>(dataProduct.public);
  const [status, setStatus] = useState<Status | null>(null);
  const [isOpen, setIsOpen] = useState(false);
  const [qrCode, setQrCode] = useState<Blob | null>(null);

  const navigate = useNavigate();

  const { activeDataProductDispatch } = useMapContext();

  const updateAccess = async (newAccess: boolean) => {
    try {
      const response = await api.put(
        `/projects/${project.id}/flights/${dataProduct.flight_id}/data_products/${dataProduct.id}/file_permission`,
        { is_public: newAccess }
      );
      if (response) {
        setStatus({ type: 'success', msg: 'Access updated' });
        activeDataProductDispatch({
          type: 'update',
          payload: { public: newAccess },
        });
        setTimeout(() => setStatus(null), 3000);
        if (refreshUrl) {
          navigate(refreshUrl, {
            state: { reload: true },
          });
        }
      } else {
        setStatus({ type: 'error', msg: 'Unable to change access' });
        setTimeout(() => setStatus(null), 3000);
        setAccessOption(!newAccess);
      }
    } catch (err) {
      setStatus({ type: 'error', msg: 'Unable to change access' });
      setTimeout(() => setStatus(null), 3000);
      setAccessOption(!newAccess);
    }
  };

  const onChange = (e) => {
    const val = e.target.value;
    if (typeof val === 'string') {
      updateAccess(val === 'true' ? true : false);
      setAccessOption(val === 'true' ? true : false);
    }
  };

  return (
    <div className="flex">
      <div
        className={`${
          qrCode ? 'flex-1' : 'w-full'
        } grid grid-flow-row auto-rows-max py-8 px-4 gap-4`}
      >
        <div>
          <h1>Share Settings</h1>
        </div>
        <fieldset>
          <legend className="sr-only">Access Control</legend>
          <div>
            <input
              type="radio"
              name="accessOption"
              value="false"
              id="accessRestricted"
              className="peer hidden [&:checked_+_label_svg]:block"
              checked={!accessOption}
              onChange={onChange}
              disabled={project.role !== 'owner'}
            />
            <label
              htmlFor="accessRestricted"
              className="flex items-center justify-between cursor-pointer peer-disabled:cursor-default rounded-lg border border-gray-50 bg-gray-100 p-4 text-sm font-medium shadow-sm hover:border-gray-200 peer-checked:border-accent3 peer-checked:ring-1 peer-checked:ring-accent3"
            >
              <div className="flex-none flex items-center gap-2 w-48">
                <svg
                  className="hidden h-5 w-5 text-slate-600"
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                    clipRule="evenodd"
                  />
                </svg>

                <p className="text-gray-700">Restricted</p>
              </div>
              <p className="text-gray-900">
                Only project members will be able to access shared links for
                this data product. Must be signed in to platform to view shared
                link.
              </p>
            </label>
          </div>
          {project.role === 'owner' ? (
            <div className="mt-2">
              <input
                type="radio"
                name="accessOption"
                value="true"
                id="accessUnrestricted"
                className="peer hidden [&:checked_+_label_svg]:block"
                checked={accessOption}
                onChange={onChange}
                disabled={project.role !== 'owner'}
              />
              <label
                htmlFor="accessUnrestricted"
                className="flex cursor-pointer items-center justify-between rounded-lg border border-gray-50 bg-gray-100 p-4 text-sm font-medium shadow-sm hover:border-gray-200 peer-checked:border-accent3 peer-checked:ring-1 peer-checked:ring-accent3"
              >
                <div className="flex-none flex items-center gap-2 w-48">
                  <svg
                    className="hidden h-5 w-5 text-slate-600"
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 20 20"
                    fill="currentColor"
                  >
                    <path
                      fillRule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                      clipRule="evenodd"
                    />
                  </svg>
                  <p className="text-gray-700">Anyone</p>
                </div>
                <p className="text-gray-900">
                  Anyone can access this data product. It can be downloaded,
                  used outside of the platform, and shared links can be viewed
                  without signing in.
                </p>
              </label>
            </div>
          ) : null}
        </fieldset>
        <div className="grid grid-cols-6 gap-4">
          <div className="col-span-2">
            <CopyURLButton
              copyText="Copy File URL"
              copiedText="Copied"
              url={dataProduct.url}
              title="Copy link that can be used to directly access the data product"
            />
          </div>
          {symbology && (
            <div className="col-span-2">
              <div className="relative">
                <button
                  type="button"
                  className="inline-flex w-full justify-center gap-x-1.5 rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 whitespace-nowrap min-w-[180px]"
                  onClick={() => setIsOpen(!isOpen)}
                >
                  Share Current Map
                  <ChevronDownIcon
                    className="-mr-1 h-5 w-5 text-gray-400"
                    aria-hidden="true"
                  />
                </button>
                {isOpen && (
                  <div
                    className="absolute right-0 z-10 mt-2 w-56 origin-top-right rounded-md bg-white shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none"
                    style={{ bottom: '100%', marginBottom: '0.5rem' }}
                  >
                    <div className="py-1">
                      <div className="px-4 py-2">
                        <CopyURLButton
                          copyText="Copy Share URL"
                          copiedText="Copied"
                          url={
                            window.origin +
                            `/sharemap?file_id=${dataProduct.id}&symbology=` +
                            btoa(JSON.stringify(symbology))
                          }
                          title="Copy link that can be used to share the current map and selected data product"
                        />
                      </div>
                      <div className="px-4 py-2">
                        <CopyShortURLButton
                          copyText="Copy Short URL"
                          copiedText="Copied"
                          dataProduct={dataProduct}
                          project={project}
                          setStatus={setStatus}
                          url={
                            window.origin +
                            `/sharemap?file_id=${
                              dataProduct.id
                            }&symbology=${btoa(JSON.stringify(symbology))}`
                          }
                        />
                      </div>
                      <div className="px-4 py-2">
                        <DownloadQRButton
                          closeShareButton={() => setIsOpen(false)}
                          dataProductId={dataProduct.id}
                          flightId={dataProduct.flight_id}
                          projectId={project.id}
                          setStatus={setStatus}
                          setQrCode={setQrCode}
                          title="Show QR Code"
                          titleOnSubmission="Generating QR Code..."
                          url={
                            window.origin +
                            `/sharemap?file_id=${
                              dataProduct.id
                            }&symbology=${btoa(JSON.stringify(symbology))}`
                          }
                        />
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
          {dataProduct.data_type === 'point_cloud' && (
            <>
              <div className="col-span-2">
                <CopyURLButton
                  copyText="Copy Share URL"
                  copiedText="Copied"
                  url={window.origin + `/sharepotree?file_id=${dataProduct.id}`}
                  title="Copy link that can be used to share the point cloud with potree"
                />
              </div>
              <div className="col-span-2">
                <DownloadQRButton
                  closeShareButton={() => setIsOpen(false)}
                  dataProductId={dataProduct.id}
                  flightId={dataProduct.flight_id}
                  projectId={project.id}
                  setStatus={setStatus}
                  setQrCode={setQrCode}
                  title="Show QR Code"
                  titleOnSubmission="Generating QR Code..."
                  url={window.origin + `/sharepotree?file_id=${dataProduct.id}`}
                />
              </div>
            </>
          )}
        </div>
        {status ? <Alert alertType={status.type}>{status.msg}</Alert> : null}
      </div>
      {qrCode && (
        <div className="flex flex-col items-center justify-center p-4 gap-4 w-48">
          <img
            className="w-full"
            src={URL.createObjectURL(qrCode)}
            alt="QR Code"
          />
          <Button
            type="button"
            size="sm"
            icon="qrcode"
            onClick={() => createAndClickDownloadLink(qrCode, 'qrcode.png')}
            aria-label="Download QR Code"
          >
            Download
          </Button>
        </div>
      )}
    </div>
  );
}
