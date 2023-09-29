import { useEffect, useState } from 'react';
import axios from 'axios';
import { Formik, Form } from 'formik';
import { useLoaderData, useNavigate } from 'react-router-dom';

import Alert from '../../Alert';
import { Button, OutlineButton } from '../../Buttons';
import Card from '../../Card';
import DrawFieldMap from '../../maps/DrawFieldMap';
import FileUpload from '../../FileUpload';
import { SelectField, TextField } from '../../InputFields';
import { Team } from '../teams/Teams';

import initialValues from './initialValues';
import validationSchema from './validationSchema';
import HintText from '../../HintText';

export async function loader() {
  const response = await axios.get('/api/v1/teams');
  if (response) {
    const teams = response.data;
    teams.unshift({ title: 'No team', id: '' });
    return teams;
  } else {
    return [];
  }
}

type Coordinates = number[][];

export interface GeoJSONFeature {
  type: string;
  geometry: {
    type: string;
    coordinates: Coordinates[] | Coordinates[][];
  };
  properties: {
    [key: string]: string;
  };
}

export interface FeatureCollection {
  type: 'FeatureCollection';
  features: GeoJSON.Feature[];
}

export interface Location {
  geojson: GeoJSONFeature;
  center: {
    lat: number;
    lng: number;
  };
}

export type SetLocation = React.Dispatch<React.SetStateAction<Location | null>>;

function coordArrayToWKT(coordArray: Coordinates[] | Coordinates[][]) {
  let wkt: string[][] = [];
  coordArray[0].forEach((coordPair) => {
    wkt.push([`${coordPair[0]} ${coordPair[1]}`]);
  });
  return wkt.join();
}

export default function ProjectForm({
  editMode = false,
  projectId = '',
}: {
  editMode?: boolean;
  projectId?: string;
}) {
  const navigate = useNavigate();
  const teams = useLoaderData() as Team[];
  const [location, setLocation] = useState<Location | null>(null);
  const [open, setOpen] = useState(false);
  const [uploadResponse, setUploadResponse] = useState<FeatureCollection | null>(null);

  useEffect(() => {
    if (uploadResponse) setOpen(true);
  }, [uploadResponse]);

  return (
    <div className="p-4">
      <Card>
        <Formik
          initialValues={initialValues}
          validationSchema={validationSchema}
          onSubmit={async (values, { setSubmitting }) => {
            try {
              const data = {
                title: values.title,
                description: values.description,
                location_id: values.locationId,
                planting_date: values.plantingDate,
                ...(values.harvestDate && { harvest_date: values.harvestDate }),
                ...(values.teamId && { team_id: values.teamId }),
              };
              const response = editMode
                ? await axios.put(`/api/v1/projects/${projectId}`, data)
                : await axios.post('/api/v1/projects', data);
              if (response) {
                editMode ? navigate(`/projects/${projectId}`) : navigate('/projects');
              } else {
                // do something
              }
            } catch (err) {
              if (axios.isAxiosError(err)) {
                console.error(err);
              } else {
                // do something
              }
            }
            setSubmitting(false);
          }}
        >
          {({
            isSubmitting,
            setFieldTouched,
            setFieldValue,
            setStatus,
            status,
            values,
          }) => (
            <Form>
              <div className="grid grid-cols-2 gap-8">
                <div className="min-h-[600px] grid grid-rows-6 gap-4">
                  <div className="row-span-4">
                    <DrawFieldMap
                      featureCollection={uploadResponse}
                      location={location}
                      setLocation={setLocation}
                    />
                  </div>
                  <div className="row-span-1">
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
                            const response = await axios.post<GeoJSONFeature>(
                              '/api/v1/locations',
                              data
                            );
                            if (response) {
                              setFieldTouched('locationId', true);
                              setFieldValue('locationId', response.data.properties.id);
                            }
                            setOpen(false);
                          } catch (err) {
                            setStatus({
                              type: 'error',
                              msg: 'Unable to save location',
                            });
                          }
                        } else {
                          setStatus({
                            type: 'warning',
                            msg: 'Must draw field boundary before saving',
                          });
                        }
                      }}
                    >
                      {values.locationId ? 'Update Field' : 'Save Field'}
                    </Button>
                  </div>
                  <div className="row-span-1">
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
                </div>
                <div>
                  <TextField label="Title" name="title" />
                  <TextField
                    type="textarea"
                    label="Description"
                    name="description"
                    placeholder="Enter a description of the project..."
                  />
                  <div className="grid grid-cols-2 gap-4">
                    <TextField type="date" label="Planting date" name="plantingDate" />
                    <TextField
                      type="date"
                      label="Harvest date"
                      name="harvestDate"
                      required={false}
                    />
                  </div>
                  {teams.length > 0 ? (
                    <SelectField
                      label="Team"
                      name="teamId"
                      options={teams.map((team) => ({
                        label: team.title,
                        value: team.id,
                      }))}
                    />
                  ) : null}
                </div>
              </div>
              {status && status.type && status.msg ? (
                <div className="mt-4">
                  <Alert alertType={status.type}>{status.msg}</Alert>
                </div>
              ) : null}
              <div className="flex justify-center mt-4 w-full">
                <div className="w-96">
                  <Button type="submit" disabled={isSubmitting}>
                    Create
                  </Button>
                </div>
              </div>
            </Form>
          )}
        </Formik>
      </Card>
    </div>
  );
}
