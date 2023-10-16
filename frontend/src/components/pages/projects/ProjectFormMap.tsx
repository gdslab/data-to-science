import axios from 'axios';
import { ErrorMessage, useFormikContext } from 'formik';
import { useState } from 'react';

import { Button, OutlineButton } from '../../Buttons';
import DrawFieldMap from '../../maps/DrawFieldMap';
import FileUpload from '../../FileUpload';
import { Coordinates, FeatureCollection, GeoJSONFeature } from './ProjectForm';
import HintText from '../../HintText';
import { Location } from './ProjectForm';

function coordArrayToWKT(coordArray: Coordinates[] | Coordinates[][]) {
  let wkt: string[][] = [];
  coordArray[0].forEach((coordPair) => {
    wkt.push([`${coordPair[0]} ${coordPair[1]}`]);
  });
  return wkt.join();
}

interface Props {
  isUpdate?: boolean;
  location: Location | null;
  locationId: string;
  open: boolean;
  projectId?: string;
  setLocation: React.Dispatch<React.SetStateAction<Location | null>>;
  setOpen: React.Dispatch<React.SetStateAction<boolean>>;
}

export default function ProjectFormMap({
  isUpdate = false,
  location,
  locationId,
  open,
  projectId = '',
  setLocation,
  setOpen,
}: Props) {
  const [uploadResponse, setUploadResponse] = useState<FeatureCollection | null>(null);
  const { setFieldTouched, setFieldValue, setStatus } = useFormikContext();

  return (
    <div className="grid grid-rows-auto gap-4">
      <div className="h-96">
        <DrawFieldMap
          featureCollection={uploadResponse}
          location={location}
          setLocation={setLocation}
          setUploadResponse={setUploadResponse}
        />
      </div>
      <div>
        <ErrorMessage
          className="text-red-500 text-sm"
          name="locationId"
          component="span"
        />
        {uploadResponse ? (
          <div className="mb-2">
            <span className="font-semibold text-slate-700">
              Click on the project's field boundary.
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
            <FileUpload
              endpoint={`/api/v1/locations/upload`}
              open={open}
              onSuccess={() => setOpen(false)}
              restrictions={{
                allowedFileTypes: ['.zip'],
                maxNumberOfFiles: 1,
                minNumberOfFiles: 1,
              }}
              setOpen={setOpen}
              setUploadResponse={setUploadResponse}
              uploadType="shp"
            />
          </div>
        )}
        <Button
          size="sm"
          onClick={async (e) => {
            e.preventDefault();
            setStatus(null);
            if (location) {
              try {
                const data = {
                  center_x: location.center.lng,
                  center_y: location.center.lat,
                  geom: `SRID=4326;POLYGON((${coordArrayToWKT(
                    location.geojson.geometry.coordinates
                  )}))`,
                };
                const response = !isUpdate
                  ? await axios.post<GeoJSONFeature>('/api/v1/locations', data)
                  : await axios.put<GeoJSONFeature>(
                      `/api/v1/locations/${projectId}/${locationId}`,
                      data
                    );
                if (response) {
                  setFieldTouched('locationId', true);
                  setFieldValue('locationId', response.data.properties.id);
                  setStatus({
                    type: 'success',
                    msg: isUpdate ? 'Field updated' : 'Field saved',
                  });
                  setUploadResponse(null);
                }
                setOpen(false);
              } catch (err) {
                setStatus({
                  type: 'error',
                  msg: 'Unable to save location',
                });
                setUploadResponse(null);
              }
            } else {
              setStatus({
                type: 'warning',
                msg: 'Must draw field boundary before saving or select an uploaded field by clicking the boundary',
              });
            }
          }}
        >
          {locationId ? 'Update Field' : 'Save Field'}
        </Button>
      </div>
    </div>
  );
}
