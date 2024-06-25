import axios, { isAxiosError, AxiosResponse } from 'axios';
import { useEffect, useState } from 'react';
import { FormProvider, SubmitHandler, useForm } from 'react-hook-form';
import { useParams } from 'react-router-dom';
import { XMarkIcon } from '@heroicons/react/24/outline';
import { yupResolver } from '@hookform/resolvers/yup';

import Alert, { Status } from '../../../Alert';
import { Button } from '../../../Buttons';
import MapLayerFileInput from './MapLayerFileInput';
import Modal from '../../../Modal';
import { useProjectContext } from '../ProjectContext';
import { validationSchema } from './validationSchema';
import { MapLayerFeatureCollection } from '../Project';

export interface MapLayerFormInput {
  layerName: string;
  geojson: string;
}

const defaultValues = {
  layerName: '',
  geojson: '',
};

export default function MapLayerUpload() {
  const [mlFileInputKey, setMLFileInputKey] = useState(Date.now());
  const [open, setOpen] = useState(false);
  const [status, setStatus] = useState<Status | null>(null);
  const [uploadFile, setUploadFile] = useState<File | null>(null);

  const { projectId } = useParams();
  const { mapLayersDispatch } = useProjectContext();

  const methods = useForm<MapLayerFormInput>({
    defaultValues,
    resolver: yupResolver(validationSchema),
  });
  const {
    formState: { errors },
    handleSubmit,
    register,
    reset,
  } = methods;

  const onSubmit: SubmitHandler<MapLayerFormInput> = async (values) => {
    setStatus(null);
    try {
      const response: AxiosResponse<MapLayerFeatureCollection> = await axios.post(
        `${import.meta.env.VITE_API_V1_STR}/projects/${projectId}/vector_layers`,
        { layer_name: values.layerName, geojson: JSON.parse(values.geojson) }
      );
      if (response.status === 201) {
        setStatus({ type: 'success', msg: 'Project layer added' });
        // reset form
        reset();
        // update key for file input elem (clears out previous file)
        setMLFileInputKey(Date.now());
        setUploadFile(null);
        // update map layer context with new map layer
        mapLayersDispatch({ type: 'update', payload: [response.data] });
      } else {
        setStatus({ type: 'error', msg: 'Unable to add project layer' });
        // reset form
        reset();
        // update key for file input elem (clears out previous file)
        setMLFileInputKey(Date.now());
        setUploadFile(null);
      }
    } catch (err) {
      if (isAxiosError(err)) {
        setStatus({ type: 'error', msg: err.response?.data.detail });
      } else {
        setStatus({ type: 'error', msg: 'Unable to add project layer' });
      }
      // reset form
      reset();
      // update key for file input elem (clears out previous file)
      setMLFileInputKey(Date.now());
      setUploadFile(null);
    }
  };

  useEffect(() => {
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
            <button type="button" onClick={handleClick} title="Close upload popup">
              <XMarkIcon className="w-4 h-4 stroke-[3px]" />
            </button>
          </div>
          <div className="p-4">
            <p className="mb-4">
              Shapefile and GeoJSON datasets{' '}
              <strong>must be in the WGS84 coordinate system.</strong>
            </p>
            {/* form */}
            <FormProvider {...methods}>
              <form className="flex flex-col gap-2" onSubmit={handleSubmit(onSubmit)}>
                <div className="w-full flex justify-center">
                  <input className="hidden" {...register('layerName')} />
                  <input className="hidden" {...register('geojson')} />
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
                      disabled={errors.layerName || errors.geojson ? true : false}
                    >
                      Upload
                    </Button>
                  </div>
                </div>
                {/* Display any error messages from backend API */}
                {status && status.type && status.msg && (
                  <Alert alertType={status.type}>{status.msg}</Alert>
                )}
                {/* Display any form error messages */}
                {errors && errors.geojson && (
                  <Alert alertType="error">{errors.geojson.message}</Alert>
                )}
              </form>
            </FormProvider>
          </div>
        </div>
      </Modal>
    </div>
  );
}
