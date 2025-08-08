import { ErrorMessage, useFormikContext } from 'formik';
import { FeatureCollection } from 'geojson';
import { useEffect, useState } from 'react';

import { Button, OutlineButton } from '../../Buttons';
import DrawFieldMapNew from '../../maps/DrawFieldMap/DrawFieldMapNew';
import { GeoJSONFeature } from './Project';
import HintText from '../../HintText';
import { useProjectContext } from './ProjectContext';
import ShapefileUpload from './ShapefileUpload';

import api from '../../../api';

interface Props {
  isUpdate?: boolean;
  locationId?: string;
  projectId?: string;
}

export default function ProjectFormMap({
  isUpdate = false,
  locationId = '',
  projectId = '',
}: Props) {
  const [open, setOpen] = useState(false);
  const [featureCollection, setFeatureCollection] =
    useState<FeatureCollection | null>(null);
  const [mapboxAccessToken, setMapboxAccessToken] = useState<string>('');
  const [maptilerApiKey, setMaptilerApiKey] = useState<string>('');

  const { setFieldTouched, setFieldValue, setStatus } = useFormikContext();

  const { location } = useProjectContext();

  // Load API keys from config.json or environment variables
  useEffect(() => {
    if (
      !import.meta.env.VITE_MAPBOX_ACCESS_TOKEN ||
      !import.meta.env.VITE_MAPTILER_API_KEY
    ) {
      fetch('/config.json')
        .then((response) => response.json())
        .then((config) => {
          if (config.mapboxAccessToken) {
            setMapboxAccessToken(config.mapboxAccessToken);
          }
          if (config.maptilerApiKey) {
            setMaptilerApiKey(config.maptilerApiKey);
          }
        })
        .catch((error) => {
          console.error('Failed to load config.json:', error);
        });
    } else {
      if (import.meta.env.VITE_MAPBOX_ACCESS_TOKEN) {
        setMapboxAccessToken(import.meta.env.VITE_MAPBOX_ACCESS_TOKEN);
      }
      if (import.meta.env.VITE_MAPTILER_API_KEY) {
        setMaptilerApiKey(import.meta.env.VITE_MAPTILER_API_KEY);
      }
    }
  }, []);

  // Handle draw start callback
  const handleDrawStart = () => {
    // Clear any existing status messages
    setStatus(null);
  };

  // Handle draw end callback
  const handleDrawEnd = (feature: any) => {
    // Set success status when drawing is completed
    setStatus({
      type: 'success',
      msg: 'Field boundary drawn successfully. You can now create the project.',
    });
  };

  return (
    <div className="grid grid-rows-auto gap-4">
      <div className="h-96">
        <DrawFieldMapNew
          featureCollection={featureCollection}
          setFeatureCollection={setFeatureCollection}
          mapboxAccessToken={mapboxAccessToken}
          maptilerApiKey={maptilerApiKey}
          featureLimit={1}
          onDrawStart={handleDrawStart}
          onDrawEnd={handleDrawEnd}
        />
      </div>
      <div>
        <ErrorMessage
          className="text-red-500 text-sm"
          name="location.geom"
          component="span"
        />
        {featureCollection && featureCollection.features.length > 1 ? (
          <div className="mb-2">
            <span className="font-semibold text-slate-700">
              Multiple boundaries detected. Click on the boundary you would like
              to associate with this project.
            </span>
          </div>
        ) : (
          <div className="mb-2">
            <HintText>
              Upload your field as a GeoJSON file or a zipped shapefile.
            </HintText>
            <div className="flex gap-2">
              <OutlineButton
                size="sm"
                onClick={(e) => {
                  e.preventDefault();
                  setOpen(true);
                }}
              >
                Upload Field Boundary (.geojson, .json,.zip)
              </OutlineButton>
            </div>

            <ShapefileUpload
              endpoint={`${
                import.meta.env.VITE_API_V1_STR
              }/locations/upload_project_boundary`}
              open={open}
              onSuccess={() => setOpen(false)}
              setOpen={setOpen}
              setUploadResponse={setFeatureCollection}
            />
          </div>
        )}
        {isUpdate ? (
          <Button
            size="sm"
            onClick={async (e) => {
              e.preventDefault();
              setStatus(null);
              if (location) {
                try {
                  const response = await api.put<GeoJSONFeature>(
                    `/locations/${projectId}/${locationId}`,
                    location
                  );
                  if (response) {
                    setFieldTouched('location', true);
                    setFieldValue('location', location);
                    setStatus({
                      type: 'success',
                      msg: 'Field updated',
                    });
                    setFeatureCollection(null);
                  }
                  setOpen(false);
                } catch (err) {
                  setStatus({
                    type: 'error',
                    msg: 'Unable to save location',
                  });
                  setFeatureCollection(null);
                }
              } else {
                setStatus({
                  type: 'warning',
                  msg: 'Must draw field boundary before saving or select an uploaded field by clicking the boundary',
                });
              }
            }}
          >
            Update Field
          </Button>
        ) : null}
      </div>
    </div>
  );
}
