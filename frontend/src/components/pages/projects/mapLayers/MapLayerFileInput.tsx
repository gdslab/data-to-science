import { useFormikContext } from 'formik';
import { FeatureCollection } from 'geojson';
import { ChangeEvent } from 'react';

import { Status } from '../../../Alert';
import { shpToGeoJSON } from './utils';

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
  setStatus,
}: {
  inputKey: number;
  setStatus: React.Dispatch<React.SetStateAction<Status | null>>;
}) {
  const { setFieldValue, setFieldTouched, setTouched } = useFormikContext();
  function clearFields() {
    setFieldValue('geojson', null);
    setFieldValue('layerName', '');
    setFieldTouched('geojson', false);
    setFieldTouched('layerName', false);
  }

  /**
   * Reads contents of uploaded GeoJSON.
   * @param file GeoJSON file.
   */
  function handleFileRead(file: File) {
    const fileReader = new FileReader();
    fileReader.onload = () => {
      const result = fileReader.result;
      if (result && typeof result === 'string') {
        try {
          const parsedGeoJSON: FeatureCollection = JSON.parse(result);
          // display error if no features included in collection
          if (parsedGeoJSON.features.length < 1) {
            setStatus({
              type: 'error',
              msg: 'Feature Collection must have at least one feature',
            });
            clearFields();
          } else if (!isFeatureGeometryMatching(parsedGeoJSON)) {
            // display error if features in collection do not have same geometry type
            setStatus({
              type: 'error',
              msg: 'Features in Feature Collection must have same geometry type',
            });
            clearFields();
          } else {
            setFieldValue('geojson', parsedGeoJSON);
            setFieldValue('layerName', file.name);
          }
        } catch (err) {
          setStatus({ type: 'error', msg: 'Unable to parse uploaded GeoJSON' });
          clearFields();
        }
      } else {
        setStatus({ type: 'error', msg: 'Unable to parse uploaded GeoJSON' });
        clearFields();
      }
    };
    fileReader.onerror = () => {
      setStatus({ type: 'error', msg: 'Unable to parse uploaded GeoJSON' });
      clearFields();
    };
    fileReader.readAsText(file);
  }

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    setStatus(null);
    setTouched({});

    const files = event.target.files;
    if (files && files.length > 0) {
      const file = files[0];
      if (file.type === 'application/zip') {
        shpToGeoJSON(file)
          .then((data) => {
            if (data) {
              setFieldValue('geojson', data);
              setFieldValue('layerName', file.name);
            } else {
              clearFields();
            }
          })
          .catch((err) => {
            setStatus({
              type: 'error',
              msg: err.message ? err.message : 'Unable to process uploaded file',
            });
            clearFields();
          });
      } else if (
        file.type === 'application/geo+json' ||
        file.type === 'application/json'
      ) {
        handleFileRead(file);
      }
    }
  }

  return (
    <div>
      <label
        htmlFor="uploadVectorLayer"
        className="block text-sm text-gray-400 font-bold pt-2 pb-1"
      >
        Upload Vector Layer
      </label>
      <input
        key={inputKey.toString()}
        type="file"
        id="uploadVectorLayer"
        name="uploadVectorLayer"
        accept="application/geo+json,application/json,application/zip"
        multiple={false}
        onChange={handleFileChange}
      />
    </div>
  );
}
