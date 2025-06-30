import { Form, Formik } from 'formik';
import { useEffect, useState } from 'react';
import { useParams, useRevalidator } from 'react-router-dom';
import { WrenchScrewdriverIcon } from '@heroicons/react/24/outline';

import Alert, { Status } from '../../../../../Alert';
import { Button } from '../../../../../Buttons';
import DataProductBandForm from './DataProductBandForm';
import Modal from '../../../../../Modal';
import HintText from '../../../../../HintText';
import { useFlightContext } from '../../FlightContext/FlightContext';
import { DataProduct } from '../../Project';
import { isElevationDataProduct } from '../../../../../maps/utils';
import {
  HillshadeTools,
  MultiSpectralTools,
  PointCloudTools,
  RGBTools,
  ZonalStatisticTools,
} from './ToolboxTools';

import api from '../../../../../../api';

export interface ToolboxFields {
  chm: boolean;
  chmResolution: number;
  chmPercentile: number;
  dem_id: string;
  dtm: boolean;
  dtmResolution: number;
  dtmRigidness: number;
  exg: boolean;
  exgRed: number;
  exgGreen: number;
  exgBlue: number;
  hillshade: boolean;
  ndvi: boolean;
  ndviNIR: number;
  ndviRed: number;
  vari: boolean;
  variRed: number;
  variGreen: number;
  variBlue: number;
  zonal: boolean;
  zonal_layer_id: string;
}

const getNumOfBands = (dataProduct: DataProduct) => {
  return dataProduct.stac_properties.raster.length;
};

const getInitialValues = (
  dataProduct: DataProduct,
  otherDataProducts: DataProduct[] = []
) => {
  const eo = dataProduct.stac_properties?.eo ?? [];

  const findBandIndex = (description: string, defaultIndex: number) => {
    const idx = eo.findIndex(
      (band) => band.description.toLowerCase() === description
    );
    return idx === -1 ? defaultIndex : idx;
  };

  const redBandIndex = findBandIndex('red', 0);
  const greenBandIndex = findBandIndex('green', 1);
  const blueBandIndex = findBandIndex('blue', 2);
  const nirBandIndex = findBandIndex('nir', 3);

  // Find first available elevation data product
  const firstElevationProduct = otherDataProducts.find(isElevationDataProduct);

  return {
    chm: false,
    chmResolution: 0.5,
    chmPercentile: 98,
    dem_id: firstElevationProduct?.id ?? '',
    dtm: false,
    dtmResolution: 0.5,
    dtmRigidness: 2,
    exg: false,
    exgRed: redBandIndex + 1,
    exgGreen: greenBandIndex + 1,
    exgBlue: blueBandIndex + 1,
    hillshade: false,
    ndvi: false,
    ndviNIR: nirBandIndex + 1,
    ndviRed: redBandIndex + 1,
    vari: false,
    variRed: redBandIndex + 1,
    variGreen: greenBandIndex + 1,
    variBlue: blueBandIndex + 1,
    zonal: false,
    zonal_layer_id: '',
  } as ToolboxFields;
};

export default function ToolboxModal({
  dataProduct,
  otherDataProducts,
  tableView = false,
}: {
  dataProduct: DataProduct;
  otherDataProducts: DataProduct[];
  tableView?: boolean;
}) {
  const [open, setOpen] = useState(false);
  const [status, setStatus] = useState<Status | null>(null);
  const { flight } = useFlightContext();
  const { projectId, flightId } = useParams();
  const revalidator = useRevalidator();

  const isPointCloud = dataProduct.data_type === 'point_cloud';

  useEffect(() => {
    setStatus(null);
  }, []);

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
          <div className="flex flex-col gap-4">
            {!isPointCloud && <DataProductBandForm dataProduct={dataProduct} />}
            <Formik
              initialValues={getInitialValues(dataProduct, otherDataProducts)}
              onSubmit={async (values, actions) => {
                setStatus(null);
                if (projectId && flightId && dataProduct.id) {
                  try {
                    const response = await api.post(
                      `/projects/${projectId}/flights/${flightId}/data_products/${dataProduct.id}/tools`,
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
                    setStatus({
                      type: 'error',
                      msg: 'Unable to complete request',
                    });
                  }
                } else {
                  setStatus({
                    type: 'error',
                    msg: 'Unable to complete request',
                  });
                }
              }}
            >
              {({ dirty, isSubmitting, values }) => (
                <Form className="grid grid-row-auto gap-4">
                  <HintText>Select data products to be generated</HintText>
                  {/* rgb tools */}
                  {flight &&
                    !isPointCloud &&
                    (flight.sensor.toLowerCase() === 'rgb' ||
                      flight.sensor.toLowerCase() === 'multispectral') &&
                    getNumOfBands(dataProduct) > 2 && (
                      <RGBTools dataProduct={dataProduct} />
                    )}
                  {/* multispectral tools */}
                  {flight &&
                    !isPointCloud &&
                    flight.sensor.toLowerCase() === 'multispectral' &&
                    getNumOfBands(dataProduct) > 2 && (
                      <MultiSpectralTools dataProduct={dataProduct} />
                    )}
                  {/* hillshade and zonal statistic tools */}
                  {flight &&
                    !isPointCloud &&
                    getNumOfBands(dataProduct) === 1 && (
                      <>
                        <HillshadeTools />
                        <ZonalStatisticTools dataProductId={dataProduct.id} />
                      </>
                    )}
                  {/* point cloud tools */}
                  {flight && isPointCloud && (
                    <PointCloudTools otherDataProducts={otherDataProducts} />
                  )}
                  <Button
                    type="submit"
                    disabled={
                      (!values.exg &&
                        !values.ndvi &&
                        !values.vari &&
                        !values.chm &&
                        !values.dtm &&
                        !values.hillshade &&
                        !values.zonal) ||
                      (values.zonal && !values.zonal_layer_id) ||
                      (values.chm && !values.dem_id) ||
                      !dirty
                    }
                    size="sm"
                  >
                    {!isSubmitting ? 'Start' : 'Starting process...'}
                  </Button>
                </Form>
              )}
            </Formik>
            {status && <Alert alertType={status.type}>{status.msg}</Alert>}
          </div>
        </div>
      </Modal>
    </div>
  );
}
