import axios from 'axios';
import { ErrorMessage, useFormikContext } from 'formik';
import { useState } from 'react';

import { Button, OutlineButton } from '../../Buttons';
import DrawFieldMap from '../../maps/DrawFieldMap';
import { FeatureCollection, GeoJSONFeature } from './Project';
import HintText from '../../HintText';
import { useProjectContext } from './ProjectContext';
import ShapefileUpload from './ShapefileUpload';

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
  const [featureCollection, setFeatureCollection] = useState<FeatureCollection | null>(
    null
  );

  const { setFieldTouched, setFieldValue, setStatus } = useFormikContext();

  const { location } = useProjectContext();

  return (
    <div className="grid grid-rows-auto gap-4">
      <div className="h-96">
        <DrawFieldMap
          isUpdate={isUpdate}
          featureCollection={featureCollection}
          setFeatureCollection={setFeatureCollection}
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
              Multiple boundaries detected. Click on the boundary you would like to
              associate with this project.
            </span>
          </div>
        ) : (
          <div className="mb-2">
            <HintText>
              Use the below button to upload your field in a zipped shapefile.
            </HintText>
            <OutlineButton
              size="sm"
              onClick={(e) => {
                e.preventDefault();
                setOpen(true);
              }}
            >
              Upload Shapefile (.zip)
            </OutlineButton>
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
                  const response = await axios.put<GeoJSONFeature>(
                    `${
                      import.meta.env.VITE_API_V1_STR
                    }/locations/${projectId}/${locationId}`,
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
