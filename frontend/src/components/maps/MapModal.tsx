import { Fragment, useRef, useState } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import axios from 'axios';
import { useFormikContext } from 'formik';

import DrawFieldMap from './DrawFieldMap';
import Alert, { Status } from '../Alert';

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

interface Location {
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

interface Props {
  featureCollection: FeatureCollection | null;
  open: boolean;
  setOpen: React.Dispatch<React.SetStateAction<boolean>>;
}

export default function MapModal({ featureCollection, open, setOpen }: Props) {
  const cancelButtonRef = useRef(null);
  const { setFieldValue, setFieldTouched } = useFormikContext();
  const [location, setLocation] = useState<Location | null>(null);
  const [status, setStatus] = useState<Status | null>(null);
  return (
    <Transition.Root show={open} as={Fragment}>
      <Dialog
        as="div"
        className="relative z-10"
        initialFocus={cancelButtonRef}
        onClose={setOpen}
      >
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" />
        </Transition.Child>

        <div className="fixed inset-0 z-10 overflow-y-auto">
          <div className="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
              enterTo="opacity-100 translate-y-0 sm:scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 translate-y-0 sm:scale-100"
              leaveTo="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
            >
              <Dialog.Panel className="relative transform overflow-hidden rounded-lg bg-white text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-lg">
                <div className="bg-white px-4 pb-4 pt-5 sm:p-6 sm:pb-4">
                  <DrawFieldMap
                    featureCollection={featureCollection}
                    location={location}
                    setLocation={setLocation}
                  />
                </div>
                {status && status.type && status.msg ? (
                  <div className="px-4 py-3">
                    <Alert alertType={status.type}>{status.msg}</Alert>
                  </div>
                ) : null}
                <div className="bg-gray-50 px-4 py-3 sm:flex sm:flex-row-reverse sm:px-6">
                  <button
                    type="button"
                    className="inline-flex w-full justify-center rounded-md bg-accent3 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-accent3-dark sm:ml-3 sm:w-auto"
                    onClick={async () => {
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
                          console.error(err);
                          setStatus({ type: 'error', msg: 'Unable to save location' });
                        }
                      } else {
                        setStatus({
                          type: 'warning',
                          msg: 'Must draw field boundary before saving',
                        });
                      }
                    }}
                  >
                    Save
                  </button>
                  <button
                    type="button"
                    className="mt-3 inline-flex w-full justify-center rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 sm:mt-0 sm:w-auto"
                    onClick={() => {
                      setStatus(null);
                      setLocation(null);
                      setOpen(false);
                    }}
                    ref={cancelButtonRef}
                  >
                    Cancel
                  </button>
                </div>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition.Root>
  );
}
