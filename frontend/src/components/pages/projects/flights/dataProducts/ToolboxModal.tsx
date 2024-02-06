import { Field, Form, Formik, useFormikContext } from 'formik';
import { useState } from 'react';
import { WrenchScrewdriverIcon } from '@heroicons/react/24/outline';

import { Button } from '../../../../Buttons';
import { DataProduct } from '../../ProjectDetail';
import Modal from '../../../../Modal';

import { SelectField } from '../../../../InputFields';
import HintText from '../../../../HintText';
import { useProjectContext } from '../../ProjectContext';

interface ToolboxFields {
  chm: boolean;
  exg: boolean;
  exgRed: number;
  exgGreen: number;
  exgBlue: number;
  ndvi: boolean;
  ndviNIR: number;
  ndviRed: number;
}

const EXGBandSelection = ({ dataProduct }: { dataProduct: DataProduct }) => {
  const bandOptions = dataProduct.stac_properties.eo.map((band, idx) => ({
    label: band.name,
    value: idx + 1,
  }));

  return (
    <div>
      <HintText>Select Red, Green, and Blue Bands</HintText>
      <div className="flex flex-row gap-4">
        <SelectField name="exgRed" label="Red Band" options={bandOptions} />
        <SelectField name="exgGreen" label="Green Band" options={bandOptions} />
        <SelectField name="exgBlue" label="Blue Band" options={bandOptions} />
      </div>
    </div>
  );
};

const NDVIBandSelection = ({ dataProduct }: { dataProduct: DataProduct }) => {
  const bandOptions = dataProduct.stac_properties.eo.map((band, idx) => ({
    label: band.name,
    value: idx + 1,
  }));

  return (
    <div>
      <HintText>Select Red and Near-Infrared Bands</HintText>
      <div className="flex flex-row gap-4">
        <SelectField name="ndviRed" label="Red Band" options={bandOptions} />
        <SelectField name="ndviNIR" label="NIR Band" options={bandOptions} />
      </div>
    </div>
  );
};

const RGBTools = ({ dataProduct }: { dataProduct: DataProduct }) => {
  const { values } = useFormikContext<ToolboxFields>();

  return (
    <ul>
      <li>
        <div className="flex flex-col gap-4">
          <div className="flex items-center">
            <Field id="exg-checkbox" type="checkbox" name="exg" />
            <label
              htmlFor="exg-checkbox"
              className="ms-2 text-sm font-medium text-gray-900 dark:text-gray-300"
            >
              Excess Green Vegetation Index (ExG)
            </label>
          </div>
          {values.exg ? <EXGBandSelection dataProduct={dataProduct} /> : null}
        </div>
      </li>
    </ul>
  );
};

const MultiSpectralTools = ({ dataProduct }: { dataProduct: DataProduct }) => {
  const { values } = useFormikContext<ToolboxFields>();

  return (
    <ul>
      <li>
        <div className="flex flex-col gap-4">
          <div className="flex items-center">
            <Field id="nvdi-checkbox" type="checkbox" name="ndvi" />
            <label
              htmlFor="nvdi-checkbox"
              className="ms-2 text-sm font-medium text-gray-900 dark:text-gray-300"
            >
              Normalized Difference Vegetation Index (NDVI)
            </label>
          </div>
          {values.ndvi ? <NDVIBandSelection dataProduct={dataProduct} /> : null}
        </div>
      </li>
    </ul>
  );
};

const LidarTools = () => {
  return (
    <ul>
      <li>
        <div className="flex flex-col gap-4">
          <div className="flex items-center">
            <Field id="chm-checkbox" type="checkbox" name="chm" disabled />
            <label
              htmlFor="chm-checkbox"
              className="ms-2 text-sm font-medium text-gray-900 dark:text-gray-300"
            >
              Canopy Height Model (CHM) <span className="italic">Coming soon</span>
            </label>
          </div>
        </div>
      </li>
    </ul>
  );
};

export default function ToolboxModal({ dataProduct }: { dataProduct: DataProduct }) {
  const [open, setOpen] = useState(false);
  const { flight } = useProjectContext();

  return (
    <div>
      <div
        className="flex items-center gap-2 text-sky-600 cursor-pointer"
        onClick={() => setOpen(true)}
      >
        <WrenchScrewdriverIcon className="h-6 w-6" />
        <span>Toolbox</span>
      </div>
      <Modal open={open} setOpen={setOpen}>
        <div className="p-4">
          <div className="flex flex-row items-center gap-1.5 mb-2">
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
            onSubmit={(values, actions) => {
              actions.setSubmitting(true);
              setTimeout(() => {
                actions.setSubmitting(false);
              }, 3000);
              console.log(values);
            }}
          >
            {({ isSubmitting, values }) => (
              <Form className="grid grid-row-auto gap-4">
                <HintText>Select data products to be generated</HintText>
                {/* rgb tools */}
                {flight && flight.sensor.toLowerCase() === 'rgb' ? (
                  <RGBTools dataProduct={dataProduct} />
                ) : null}
                {/* multispectral tools */}
                {flight && flight.sensor.toLowerCase() === 'multispectral' ? (
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
                  disabled={!values.exg && !values.ndvi && !values.chm}
                >
                  {isSubmitting ? 'Processing...' : 'Process'}
                </Button>
              </Form>
            )}
          </Formik>
        </div>
      </Modal>
    </div>
  );
}
