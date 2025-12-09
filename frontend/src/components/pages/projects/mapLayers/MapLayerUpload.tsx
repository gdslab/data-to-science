import { isAxiosError, AxiosResponse } from 'axios';
import { useEffect, useState } from 'react';
import { useParams } from 'react-router';
import { XMarkIcon } from '@heroicons/react/24/outline';

import Alert, { Status } from '../../../Alert';
import { Button } from '../../../Buttons';
import MapLayerFileInput from './MapLayerFileInput';
import Modal from '../../../Modal';
import { MapLayerFeatureCollection } from '../Project';

import api from '../../../../api';

export default function MapLayerUpload() {
  const [isUploading, setIsUploading] = useState(false);
  // eslint-disable-next-line react-hooks/purity
  const [mlFileInputKey, setMLFileInputKey] = useState(Date.now());
  const [open, setOpen] = useState(false);
  const [status, setStatus] = useState<Status | null>(null);
  const [uploadFile, setUploadFile] = useState<File | null>(null);

  const { projectId } = useParams();

  const onSubmit = async (event) => {
    event.preventDefault();
    setStatus(null);
    if (uploadFile) {
      setIsUploading(true);
      try {
        const formData = new FormData();
        formData.append('file', uploadFile);

        const headers = { 'Content-Type': 'multipart/form-data' };

        const response: AxiosResponse<MapLayerFeatureCollection> =
          await api.post(`/projects/${projectId}/vector_layers`, formData, {
            headers,
          });

        if (response.status === 202) {
          setStatus({
            type: 'success',
            msg: 'Your uploaded map layer will be added once it has been processed.',
          });
          // update key for file input elem (clears out previous file)
          setMLFileInputKey(Date.now());
          setUploadFile(null);
        } else {
          setStatus({ type: 'error', msg: 'Unable to add map layer' });
          // update key for file input elem (clears out previous file)
          setMLFileInputKey(Date.now());
          setUploadFile(null);
        }
        setIsUploading(false);
      } catch (err) {
        if (isAxiosError(err)) {
          if (typeof err.response?.data.detail === 'string') {
            setStatus({ type: 'error', msg: err.response?.data.detail });
          } else {
            setStatus({ type: 'error', msg: 'Unable to add map layer' });
          }
        } else {
          setStatus({ type: 'error', msg: 'Unable to add map layer' });
        }
        // update key for file input elem (clears out previous file)
        setMLFileInputKey(Date.now());
        setUploadFile(null);
        setIsUploading(false);
      }
    } else {
      setStatus({ type: 'warning', msg: 'Must select a file first' });
      setIsUploading(false);
    }
  };

  useEffect(() => {
    setUploadFile(null);
    setStatus(null);
  }, [open]);

  function handleClick() {
    setOpen(!open);
  }

  return (
    <div className="w-full flex justify-center">
      <Button type="button" size="sm" onClick={handleClick}>
        Add New Map Layer
      </Button>
      <Modal open={open} setOpen={setOpen}>
        <div className="flex flex-col">
          <div className="flex items-center justify-between bg-gray-300 p-4">
            <span className="text-primary font-bold">Upload Vector Layer</span>
            <button
              type="button"
              className="cursor-pointer"
              onClick={handleClick}
              title="Close upload popup"
            >
              <XMarkIcon className="w-4 h-4 stroke-[3px]" />
            </button>
          </div>
          <div className="p-4">
            <p className="mb-4">
              Shapefile and GeoJSON datasets must be in a{' '}
              <strong>geographic coordinate system</strong> that uses the{' '}
              <strong>WGS84 datum</strong> (e.g., EPSG:4326).
            </p>
            {/* form */}

            <form className="flex flex-col gap-2" onSubmit={onSubmit}>
              <div className="w-full flex justify-center">
                <MapLayerFileInput
                  inputKey={mlFileInputKey}
                  setStatus={setStatus}
                  uploadFile={uploadFile}
                  setUploadFile={setUploadFile}
                />
              </div>
              {/* Submit button */}
              <div className="w-full flex justify-end">
                <div className="w-36">
                  <Button
                    type="submit"
                    size="sm"
                    disabled={isUploading || !uploadFile}
                  >
                    {isUploading ? 'Uploading...' : 'Upload'}
                  </Button>
                </div>
              </div>
              {/* Display any error messages from backend API */}
              {status && status.type && status.msg && (
                <Alert alertType={status.type}>{status.msg}</Alert>
              )}
            </form>
          </div>
        </div>
      </Modal>
    </div>
  );
}
