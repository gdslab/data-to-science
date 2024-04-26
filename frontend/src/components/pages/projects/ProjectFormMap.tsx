import axios from 'axios';
import { ErrorMessage, useFormikContext } from 'formik';
import { useState } from 'react';

import { Button, OutlineButton } from '../../Buttons';
import DrawFieldMap from '../../maps/DrawFieldMap';
import { Coordinates, FeatureCollection, GeoJSONFeature } from './Project';
import HintText from '../../HintText';
import { useProjectContext } from './ProjectContext';
import ShapefileUpload from './ShapefileUpload';

export function coordArrayToWKT(coordArray: Coordinates[] | Coordinates[][]) {
  let wkt: string[][] = [];
  coordArray[0].forEach((coordPair) => {
    wkt.push([`${coordPair[0]} ${coordPair[1]}`]);
  });
  return wkt.join();
}

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
              endpoint={`/api/v1/locations/upload`}
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
                  const data = {
                    center_x: location.properties.center_x,
                    center_y: location.properties.center_y,
                    geom: `SRID=4326;POLYGON((${coordArrayToWKT(
                      location.geometry.coordinates
                    )}))`,
                  };
                  const response = await axios.put<GeoJSONFeature>(
                    `/api/v1/locations/${projectId}/${locationId}`,
                    data
                  );
                  if (response) {
                    setFieldTouched('location', true);
                    setFieldValue('location', data);
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
