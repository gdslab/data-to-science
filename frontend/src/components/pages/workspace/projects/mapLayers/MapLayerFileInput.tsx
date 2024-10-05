import { FeatureCollection } from 'geojson';
import { ChangeEvent } from 'react';

import { Status } from '../../../../Alert';
import ConnectForm from '../../../../ConnectForm';
import { MapLayerFormInput } from './MapLayerUpload';
import { shpToGeoJSON } from './utils';

import uploadPageIcon from '../../../../../assets/upload-page-icon.svg';
import { UseFormSetError, UseFormSetValue } from 'react-hook-form';

function isFeatureGeometryMatching(featureCollection: FeatureCollection): boolean {
  let geometryMatches = true;
  const firstFeatureGeometryType = featureCollection.features[0].geometry.type;
  // check if each feature matches first feature's geometry type
  for (const feature of featureCollection.features) {
    if (feature.geometry.type !== firstFeatureGeometryType) {
      geometryMatches = false;
      break;
    }
  }

  return geometryMatches;
}

export default function MapLayerFileInput({
  inputKey,
  uploadFile,
  setIsProcessing,
  setStatus,
  setUploadFile,
}: {
  inputKey: number;
  uploadFile: File | null;
  setIsProcessing: React.Dispatch<React.SetStateAction<boolean>>;
  setStatus: React.Dispatch<React.SetStateAction<Status | null>>;
  setUploadFile: React.Dispatch<React.SetStateAction<File | null>>;
}) {
  function clearFields(setValue: UseFormSetValue<MapLayerFormInput>) {
    setValue('geojson', '');
    setValue('layerName', '');
  }

  /**
   * Reads contents of uploaded GeoJSON.
   * @param file GeoJSON file.
   */
  function handleFileRead(
    file: File,
    setError: UseFormSetError<MapLayerFormInput>,
    setValue: UseFormSetValue<MapLayerFormInput>
  ) {
    const fileReader = new FileReader();
    fileReader.onload = () => {
      const result = fileReader.result;
      if (result && typeof result === 'string') {
        try {
          const parsedGeoJSON: FeatureCollection = JSON.parse(result);
          // display error if no features included in collection
          if (parsedGeoJSON.features.length < 1) {
            setError('geojson', {
              type: 'custom',
              message: 'Feature Collection must have at least one feature',
            });
            clearFields(setValue);
          } else if (parsedGeoJSON.features.length > 2000) {
            setError('geojson', {
              type: 'custom',
              message: 'Feature Collection cannot contain more than 2000 features',
            });
            clearFields(setValue);
          } else if (!isFeatureGeometryMatching(parsedGeoJSON)) {
            // display error if features in collection do not have same geometry type
            setError('geojson', {
              type: 'custom',
              message: 'Features in Feature Collection must have same geometry type',
            });
            clearFields(setValue);
          } else {
            // valid geojson, update form
            setValue('geojson', result);
            setValue('layerName', file.name);
          }
          setIsProcessing(false);
        } catch (err) {
          setError('geojson', {
            type: 'custom',
            message: 'Unable to parse uploaded GeoJSON',
          });
          clearFields(setValue);
          setIsProcessing(false);
        }
      } else {
        setError('geojson', {
          type: 'custom',
          message: 'Unable to parse uploaded GeoJSON',
        });
        clearFields(setValue);
        setIsProcessing(false);
      }
    };
    fileReader.onerror = () => {
      setError('geojson', {
        type: 'custom',
        message: 'Unable to parse uploaded GeoJSON',
      });
      clearFields(setValue);
      setIsProcessing(false);
    };
    fileReader.readAsText(file);
  }

  function handleFileChange(
    event: ChangeEvent<HTMLInputElement>,
    setError: UseFormSetError<MapLayerFormInput>,
    setValue: UseFormSetValue<MapLayerFormInput>
  ) {
    setStatus(null);

    const files = event.target.files;
    if (files && files.length > 0) {
      const file = files[0];
      processFile(file, setError, setValue);
    }
  }

  function processFile(
    file: File,
    setError: UseFormSetError<MapLayerFormInput>,
    setValue: UseFormSetValue<MapLayerFormInput>
  ) {
    setIsProcessing(true);
    setUploadFile(file);
    if (
      file.type === 'application/zip' ||
      file.type === 'application/x-zip-compressed'
    ) {
      shpToGeoJSON(file)
        .then((data) => {
          if (data) {
            // valid geojson, update form
            setValue('geojson', JSON.stringify(data));
            setValue('layerName', file.name);
          } else {
            setError('geojson', {
              type: 'custom',
              message: 'Unable to process uploaded file',
            });
            clearFields(setValue);
          }
          setIsProcessing(false);
        })
        .catch((err) => {
          setError('geojson', {
            type: 'custom',
            message: err.message ? err.message : 'Unable to process uploaded file',
          });
          clearFields(setValue);
          setIsProcessing(false);
        });
    } else if (
      file.type === 'application/geo+json' ||
      file.type === 'application/json'
    ) {
      handleFileRead(file, setError, setValue);
    }
  }

  function dropHandler(
    event: React.DragEvent<HTMLDivElement>,
    setError: UseFormSetError<MapLayerFormInput>,
    setValue: UseFormSetValue<MapLayerFormInput>
  ) {
    event.preventDefault();
    setStatus(null);
    if (event.dataTransfer.items.length > 0) {
      for (let itemIdx = 0; itemIdx < event.dataTransfer.items.length; itemIdx++) {
        if (event.dataTransfer.items[itemIdx].kind === 'file') {
          const file = event.dataTransfer.items[itemIdx].getAsFile();
          if (file) {
            processFile(file, setError, setValue);
          } else {
            setStatus({ type: 'error', msg: 'Unable to process file' });
          }
        } else {
          setStatus({ type: 'error', msg: 'Must be file' });
        }
      }
    } else {
      setStatus({ type: 'warning', msg: 'Must add file to get started' });
    }
  }

  function dragOverHandler(event: React.DragEvent<HTMLDivElement>) {
    event.preventDefault();
    if (event.dataTransfer.items.length > 1) {
      event.stopPropagation();
      setStatus({
        type: 'error',
        msg: 'Cannot upload more than a single file at a time.',
      });
    }
  }

  function dragLeaveHandler(event: React.DragEvent<HTMLDivElement>) {
    event.preventDefault();
  }

  return (
    <ConnectForm>
      {({ clearErrors, setError, setValue }) => (
        <div
          className="w-96 h-64 flex flex-col items-center justify-center gap-4 rounded-lg bg-gray-50 border-dashed border-2 border-gray-400"
          onDrop={(event) => {
            // clear any form errors before processing new file
            clearErrors();
            dropHandler(event, setError, setValue);
          }}
          onDragOver={dragOverHandler}
          onDragLeave={dragLeaveHandler}
        >
          <img src={uploadPageIcon} className="h-20" alt="Selected upload document" />
          {!uploadFile && <span className="text-gray-400">No file selected.</span>}
          {uploadFile && <span className="text-gray-600">{uploadFile.name}</span>}
          <label
            htmlFor="uploadMapLayer"
            className="px-4 py-2 text-white font-semibold rounded-md bg-blue-500/90 hover:bg-blue-500 cursor-pointer"
          >
            Browse
          </label>
          <input
            className="hidden"
            key={inputKey.toString()}
            type="file"
            id="uploadMapLayer"
            name="uploadMapLayer"
            accept="application/geo+json,application/json,application/zip"
            multiple={false}
            onChange={(event) => {
              // clear any form errors before processing new file
              clearErrors();
              handleFileChange(event, setError, setValue);
            }}
          />
        </div>
      )}
    </ConnectForm>
  );
}
