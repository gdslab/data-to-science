import axios from 'axios';
import { Form, Formik } from 'formik';
import { useState } from 'react';
import { useParams, useRevalidator } from 'react-router-dom';
import { WrenchScrewdriverIcon } from '@heroicons/react/24/outline';

import Alert, { Status } from '../../../../Alert';
import { Button } from '../../../../Buttons';
import Modal from '../../../../Modal';
import HintText from '../../../../HintText';
import { useFlightContext } from '../../FlightContext/FlightContext';
import { RGBTools, MultiSpectralTools, LidarTools } from './ToolboxTools';

import { DataProduct } from '../../Project';

export interface ToolboxFields {
  chm: boolean;
  exg: boolean;
  exgRed: number;
  exgGreen: number;
  exgBlue: number;
  ndvi: boolean;
  ndviNIR: number;
  ndviRed: number;
}

const getNumOfBands = (dataProduct: DataProduct) => {
  return dataProduct.stac_properties.raster.length;
};

export default function ToolboxModal({
  dataProduct,
  tableView = false,
}: {
  dataProduct: DataProduct;
  tableView?: boolean;
}) {
  const [open, setOpen] = useState(false);
  const [status, setStatus] = useState<Status | null>(null);
  const { flight } = useFlightContext();
  const { projectId, flightId } = useParams();
  const revalidator = useRevalidator();

  return (
    <div>
      <div
        className="flex items-center gap-1 text-sky-600 cursor-pointer"
        onClick={() => setOpen(true)}
      >
        {tableView ? (
          <>
            <WrenchScrewdriverIcon className="h-4 w-4" />
            <span className="text-sm">Toolbox</span>
          </>
        ) : (
          <>
            <WrenchScrewdriverIcon className="h-6 w-6" />
            <span>Toolbox</span>
          </>
        )}
      </div>
      <Modal open={open} setOpen={setOpen}>
        <div className="p-4">
          <div className="flex flex-row items-center gap-1 mb-2">
            <WrenchScrewdriverIcon className="h-6 w-6" />
            <span className="text-xl font-bold">Toolbox</span>
          </div>
          <hr className="mb-2 border-gray-300" />
          <Formik
            initialValues={
              {
                chm: false,
                exg: false,
                exgRed: 3,
                exgGreen: 2,
                exgBlue: 1,
                ndvi: false,
                ndviNIR: 4,
                ndviRed: 3,
              } as ToolboxFields
            }
            onSubmit={async (values, actions) => {
              setStatus(null);
              if (projectId && flightId && dataProduct.id) {
                try {
                  const response = await axios.post(
                    `${
                      import.meta.env.VITE_API_V1_STR
                    }/projects/${projectId}/flights/${flightId}/data_products/${
                      dataProduct.id
                    }/tools`,
                    values
                  );
                  if (response) {
                    setStatus({
                      type: 'success',
                      msg: 'Processing has begun. You may close this window.',
                    });
                    actions.resetForm({ values: values });
                    setTimeout(() => {
                      revalidator.revalidate();
                    }, 3000);
                  }
                } catch (err) {
                  setStatus({ type: 'error', msg: 'Unable to complete request' });
                }
              } else {
                setStatus({ type: 'error', msg: 'Unable to complete request' });
              }
            }}
          >
            {({ dirty, values }) => (
              <Form className="grid grid-row-auto gap-4">
                <HintText>Select data products to be generated</HintText>
                {/* rgb tools */}
                {flight &&
                (flight.sensor.toLowerCase() === 'rgb' ||
                  flight.sensor.toLowerCase() === 'multispectral') &&
                getNumOfBands(dataProduct) > 2 ? (
                  <RGBTools dataProduct={dataProduct} />
                ) : null}
                {/* multispectral tools */}
                {flight &&
                flight.sensor.toLowerCase() === 'multispectral' &&
                getNumOfBands(dataProduct) > 2 ? (
                  <MultiSpectralTools dataProduct={dataProduct} />
                ) : null}
                {/* lidar tools */}
                {flight &&
                flight.sensor.toLowerCase() === 'lidar' &&
                dataProduct.data_type === 'dsm' ? (
                  <LidarTools />
                ) : null}
                <Button
                  type="submit"
                  disabled={(!values.exg && !values.ndvi && !values.chm) || !dirty}
                >
                  Run
                </Button>
              </Form>
            )}
          </Formik>
          {status ? (
            <div className="mt-4">
              <Alert alertType={status.type}>{status.msg}</Alert>
            </div>
          ) : null}
        </div>
      </Modal>
    </div>
  );
}
