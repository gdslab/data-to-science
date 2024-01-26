import axios from 'axios';
import { useState } from 'react';

import Alert, { Status } from '../Alert';
import { Button } from '../Buttons';
import { DataProduct } from '../pages/projects/ProjectDetail';
import { SymbologySettings, useMapContext } from './MapContext';
import { Project } from '../pages/projects/ProjectList';

export default function ShareControls({
  dataProduct,
  project,
  symbologySettings,
}: {
  dataProduct: DataProduct;
  project: Project;
  symbologySettings: SymbologySettings;
}) {
  const [accessOption, setAccessOption] = useState<boolean>(dataProduct.public);
  const [includeSymbology, setIncludeSymbology] = useState(false);
  const [isCopying, setIsCopying] = useState(false);
  const [status, setStatus] = useState<Status | null>(null);

  const { activeDataProductDispatch } = useMapContext();

  const updateAccess = async (newAccess: boolean) => {
    try {
      const response = await axios.put(
        `${import.meta.env.VITE_API_V1_STR}/projects/${project.id}/flights/${
          dataProduct.flight_id
        }/data_products/${dataProduct.id}/file_permission`,
        { is_public: newAccess }
      );
      if (response) {
        setStatus({ type: 'success', msg: 'Access updated' });
        activeDataProductDispatch({ type: 'update', payload: { public: newAccess } });
        setTimeout(() => setStatus(null), 3000);
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
    <div className="grid grid-flow-row auto-rows-max p-8 gap-4">
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
            disabled={!project.is_owner}
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
              Only project members will be able to access shared links for this data
              product. Must be signed in to platform to view shared link.
            </p>
          </label>
        </div>
        {project.is_owner ? (
          <div className="mt-2">
            <input
              type="radio"
              name="accessOption"
              value="true"
              id="accessUnrestricted"
              className="peer hidden [&:checked_+_label_svg]:block"
              checked={accessOption}
              onChange={onChange}
              disabled={!project.is_owner}
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
                Anyone can access this data product. It can be downloaded, used outside
                of the platform, and shared links can be viewed without signing in.
              </p>
            </label>
          </div>
        ) : null}
      </fieldset>
      <div className="flex items-center gap-4">
        <Button
          size="sm"
          onClick={() => {
            if (includeSymbology) {
              const newUrl =
                import.meta.env.VITE_DOMAIN +
                `/sharemap?file_id=${dataProduct.id}&symbology=` +
                btoa(JSON.stringify(symbologySettings));
              navigator.clipboard.writeText(newUrl);
            } else {
              navigator.clipboard.writeText(dataProduct.url);
            }
            setIsCopying(true);
            setTimeout(() => setIsCopying(false), 3000);
          }}
        >
          {isCopying ? 'Copied to clipboard' : 'Copy file link'}
        </Button>
        <div className="flex items-center">
          <input
            id="default-checkbox"
            type="checkbox"
            className="w-4 h-4 text-slate-600 accent-slate-600 bg-gray-100 border-gray-300 rounded focus:ring-slate-500 dark:focus:ring-slate-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
            onChange={(e) => setIncludeSymbology(e.target.checked)}
          />
          <label
            htmlFor="default-checkbox"
            className="ms-2 text-sm font-medium text-gray-900 dark:text-gray-300"
          >
            Include symbology
          </label>
        </div>
      </div>
      {status ? <Alert alertType={status.type}>{status.msg}</Alert> : null}
    </div>
  );
}
