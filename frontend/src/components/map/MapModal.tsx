import { Fragment, useRef, useState } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import axios from 'axios';

import DrawFieldMap from './DrawFieldMap';

interface Location {
  geojson: {
    geometry: {
      type: string;
      coordinates: number[][];
    };
    properties: {
      [key: string]: string;
    };
    type: string;
  };
  center: {
    lat: number;
    lng: number;
  };
}

function coordArrayToWKT(coordArray: number[][]) {
  let wkt: string[] = [];
  coordArray[0].forEach((coordPair) => {
    wkt.push([`${coordPair[0]} ${coordPair[1]}`]);
  });
  return wkt.join();
}

export default function MapModal({ open, setOpen, setFieldValue, setFieldTouched }) {
  const cancelButtonRef = useRef(null);
  const [location, setLocation] = useState<Location | null>(null);
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
                  <DrawFieldMap setLocation={setLocation} />
                </div>
                <div className="bg-gray-50 px-4 py-3 sm:flex sm:flex-row-reverse sm:px-6">
                  <button
                    type="button"
                    className="inline-flex w-full justify-center rounded-md bg-accent3 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-accent3-dark sm:ml-3 sm:w-auto"
                    onClick={async () => {
                      try {
                        const data = {
                          name: `Field ${new Date().toString()}`,
                          center: `${location?.center.lat},${location?.center.lng}`,
                          geom: `SRID=4326;POLYGON((${coordArrayToWKT(
                            location?.geojson.geometry.coordinates
                          )}))`,
                        };
                        const response = await axios.post('/api/v1/locations/', data);
                        if (response) {
                          setFieldValue('locationId', response.data.id);
                          setFieldTouched('locationId', true);
                        }
                        setOpen(false);
                      } catch (err) {
                        console.error(err);
                      }
                    }}
                  >
                    Save
                  </button>
                  <button
                    type="button"
                    className="mt-3 inline-flex w-full justify-center rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 sm:mt-0 sm:w-auto"
                    onClick={() => setOpen(false)}
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
