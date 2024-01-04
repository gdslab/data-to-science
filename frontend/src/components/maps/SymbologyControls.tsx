import axios from 'axios';
import { Field, Formik, Form } from 'formik';
import { useState } from 'react';

import { cmaps } from './cmaps';
import { Button, OutlineButton } from '../Buttons';
import { NumberField, SelectField } from '../InputFields';
import {
  DSMSymbologySettings,
  OrthoSymbologySettings,
  SymbologySettings,
  SymbologySettingsAction,
  useMapContext,
} from './MapContext';
import Modal from '../Modal';
import { DataProduct } from '../pages/projects/ProjectDetail';
import ShareControls from './ShareControls';

/**
 * Determine number of decimal places for input number field's step attribute.
 * @param {number} n Integer or floating point number.
 * @returns {string} Numeric string of step value.
 */
const findStep = (n: number): number =>
  !Number.isInteger(n)
    ? parseFloat('0.' + ''.padStart(n.toString().split('.')[1].length - 1, '0') + '1')
    : 1;

const saveSymbology = async (
  symbologyValues: SymbologySettings,
  symbologyDispatch: React.Dispatch<SymbologySettingsAction>,
  projectId: string,
  dataProduct: DataProduct,
  dataProductDispatch
) => {
  try {
    const axiosRequest = dataProduct.user_style ? axios.put : axios.post;
    const response = await axiosRequest(
      `${import.meta.env.VITE_API_V1_STR}/projects/${projectId}/flights/${
        dataProduct.flight_id
      }/data_products/${dataProduct.id}/style`,
      { settings: symbologyValues }
    );
    if (response) {
      symbologyDispatch({ type: 'update', payload: symbologyValues });
      dataProductDispatch({
        type: 'set',
        payload: {
          ...dataProduct,
          user_style: symbologyValues,
        },
      });
    } else {
      console.error('Unable to update symbology');
    }
  } catch (err) {
    console.error(err);
  }
};

function DSMSymbologyControls({
  open,
  setOpen,
}: {
  open: boolean;
  setOpen: React.Dispatch<React.SetStateAction<boolean>>;
}) {
  const {
    activeDataProduct,
    activeDataProductDispatch,
    activeProject,
    symbologySettings,
    symbologySettingsDispatch,
  } = useMapContext();
  if (activeProject && activeDataProduct) {
    const symbology = symbologySettings as DSMSymbologySettings;

    return (
      <Formik
        initialValues={symbology}
        onSubmit={(values) => {
          symbologySettingsDispatch({
            type: 'update',
            payload: values,
          });
        }}
      >
        {({ values }) => (
          <Form>
            <div className="w-full mb-4">
              <fieldset className="border border-solid border-slate-300 p-3">
                <legend className="block text-sm text-gray-400 font-bold pt-2 pb-1">
                  Color Properties
                </legend>
                <SelectField name="colorRamp" label="Color Ramp" options={cmaps} />
              </fieldset>
            </div>
            <fieldset className="border border-solid border-slate-300 p-3">
              <legend className="block text-sm text-gray-400 font-bold pt-2 pb-1">
                Min / Max Value Settings
              </legend>
              <div
                className="w-full flex flex-wrap justify-between gap-4"
                role="group"
                aria-labelledby="modeGroup"
              >
                <label className="block text-sm text-gray-600 font-bold pt-2 pb-1">
                  <Field type="radio" name="mode" value="minMax" />
                  <span className="ml-2">Min/Max</span>
                </label>
                <label className="block text-sm text-gray-600 font-bold pt-2 pb-1">
                  <Field type="radio" name="mode" value="userDefined" />
                  <span className="ml-2">User defined</span>
                </label>
                <label className="block text-sm text-gray-600 font-bold pt-2 pb-1">
                  <Field type="radio" name="mode" value="meanStdDev" />
                  <span className="ml-2">Mean +/- Std. Dev.</span>
                </label>
              </div>
              {values.mode === 'minMax' ? (
                <div className="w-full flex gap-4">
                  <div className="w-1/3">
                    <NumberField
                      name="min"
                      label="Min"
                      min={symbology.min}
                      max={symbology.max}
                      step={findStep(symbology.min)}
                      disabled
                    />
                  </div>
                  <div className="w-1/3">
                    <NumberField
                      name="max"
                      label="Max"
                      min={symbology.min}
                      max={symbology.max}
                      step={findStep(symbology.min)}
                      disabled
                    />
                  </div>
                </div>
              ) : null}
              {values.mode === 'userDefined' ? (
                <div className="w-full flex gap-4">
                  <div className="w-1/3">
                    <NumberField
                      name="userMin"
                      label="Min"
                      min={symbology.min}
                      max={symbology.max}
                      step={findStep(symbology.min)}
                      required={false}
                    />
                  </div>
                  <div className="w-1/3">
                    <NumberField
                      name="userMax"
                      label="Max"
                      min={symbology.min}
                      max={symbology.max}
                      step={findStep(symbology.min)}
                      required={false}
                    />
                  </div>
                </div>
              ) : null}
              {values.mode === 'meanStdDev' ? (
                <div className="w-full">
                  <div className="w-1/2">
                    <NumberField
                      name="meanStdDev"
                      label="Mean +/- Std. Dev. &times; "
                      min={0}
                      max={100}
                      step={0.1}
                      required={false}
                    />
                  </div>
                </div>
              ) : null}
            </fieldset>
            <div className="mt-4 flex items-center justify-between">
              <div className="w-28">
                <OutlineButton
                  type="button"
                  size="sm"
                  onClick={() =>
                    saveSymbology(
                      values,
                      symbologySettingsDispatch,
                      activeProject.id,
                      activeDataProduct,
                      activeDataProductDispatch
                    )
                  }
                >
                  Save
                </OutlineButton>
              </div>
              <div className="w-28">
                <Button size="sm" onClick={() => setOpen(true)}>
                  Share
                </Button>
                <Modal open={open} setOpen={setOpen}>
                  <ShareControls
                    currentAccess={activeDataProduct.access}
                    dataProduct={activeDataProduct}
                    projectID={activeProject.id}
                    symbologySettings={symbologySettings}
                  />
                </Modal>
              </div>
              <div className="w-28">
                <Button type="submit" size="sm">
                  Apply
                </Button>
              </div>
            </div>
          </Form>
        )}
      </Formik>
    );
  } else {
    return null;
  }
}

function OrthoSymbologyControls({
  open,
  setOpen,
}: {
  open: boolean;
  setOpen: React.Dispatch<React.SetStateAction<boolean>>;
}) {
  const {
    activeDataProduct,
    activeDataProductDispatch,
    activeProject,
    symbologySettings,
    symbologySettingsDispatch,
  } = useMapContext();
  if (activeProject && activeDataProduct) {
    const symbology = symbologySettings as OrthoSymbologySettings;
    const bandOptions = activeDataProduct.stac_properties.eo.map((band, idx) => ({
      label: band.name,
      value: idx + 1,
    }));

    return (
      <Formik
        initialValues={symbology}
        onSubmit={(values) => {
          symbologySettingsDispatch({
            type: 'update',
            payload: values,
          });
        }}
      >
        {({ values }) => (
          <Form>
            <fieldset className="border border-solid border-slate-300 p-3">
              <legend className="block text-sm text-gray-400 font-bold pt-2 pb-1">
                Min / Max Value Settings
              </legend>
              <div
                className="w-full flex flex-wrap justify-between gap-4"
                role="group"
                aria-labelledby="modeGroup"
              >
                <label className="block text-sm text-gray-600 font-bold pt-2 pb-1">
                  <Field type="radio" name="mode" value="minMax" />
                  <span className="ml-2">Min/Max</span>
                </label>
                <label className="block text-sm text-gray-600 font-bold pt-2 pb-1">
                  <Field type="radio" name="mode" value="userDefined" />
                  <span className="ml-2">User defined</span>
                </label>
                <label className="block text-sm text-gray-600 font-bold pt-2 pb-1">
                  <Field type="radio" name="mode" value="meanStdDev" />
                  <span className="ml-2">Mean +/- Std. Dev.</span>
                </label>
              </div>
              {values.mode === 'meanStdDev' ? (
                <div className="w-full">
                  <div className="w-1/2">
                    <NumberField
                      name="meanStdDev"
                      label="Mean +/- Std. Dev. &times; "
                      min={0}
                      max={100}
                      step={0.1}
                      required={false}
                    />
                  </div>
                </div>
              ) : null}
            </fieldset>
            <fieldset className="border border-solid border-slate-300 p-3">
              <legend className="block text-sm text-gray-400 font-bold pt-2 pb-1">
                RGB Properties
              </legend>
              <div className="flex flex-col gap-4">
                <div className="grid grid-cols-3 gap-4">
                  <div className="grid grid-rows-3 gap-1.5 border-2 border-dotted border-red-500 rounded-md p-1.5">
                    <SelectField name="red.idx" label="Red" options={bandOptions} />
                    <NumberField
                      name={values.mode === 'userDefined' ? 'red.userMin' : 'red.min'}
                      label="Min"
                      min={0}
                      max={255}
                      step={
                        activeDataProduct.stac_properties.raster[0].data_type == 'unit8'
                          ? 1
                          : 0.1
                      }
                      disabled={values.mode !== 'userDefined'}
                      required={false}
                    />
                    <NumberField
                      name={values.mode === 'userDefined' ? 'red.userMax' : 'red.max'}
                      label="Max"
                      min={symbology.red.min}
                      max={symbology.red.max}
                      step={
                        activeDataProduct.stac_properties.raster[0].data_type == 'unit8'
                          ? 1
                          : 0.1
                      }
                      disabled={values.mode !== 'userDefined'}
                      required={false}
                    />
                  </div>
                  <div className="grid grid-rows-3 gap-1.5 border-2 border-dotted border-green-500 rounded-md p-1.5">
                    <SelectField name="green.idx" label="Green" options={bandOptions} />
                    <NumberField
                      name={
                        values.mode === 'userDefined' ? 'green.userMin' : 'green.min'
                      }
                      label="Min"
                      min={symbology.green.min}
                      max={symbology.green.max}
                      step={
                        activeDataProduct.stac_properties.raster[0].data_type == 'unit8'
                          ? 1
                          : 0.1
                      }
                      disabled={values.mode !== 'userDefined'}
                      required={false}
                    />
                    <NumberField
                      name={
                        values.mode === 'userDefined' ? 'green.userMax' : 'green.max'
                      }
                      label="Max"
                      min={symbology.green.min}
                      max={symbology.green.max}
                      step={
                        activeDataProduct.stac_properties.raster[0].data_type == 'unit8'
                          ? 1
                          : 0.1
                      }
                      disabled={values.mode !== 'userDefined'}
                      required={false}
                    />
                  </div>
                  <div className="grid grid-rows-3 gap-1.5 border-2 border-dotted border-blue-500 rounded-md p-1.5">
                    <SelectField name="blue.idx" label="Blue" options={bandOptions} />
                    <NumberField
                      name={values.mode === 'userDefined' ? 'blue.userMin' : 'blue.min'}
                      label="Min"
                      min={symbology.blue.min}
                      max={symbology.blue.max}
                      step={0.1}
                      disabled={values.mode !== 'userDefined'}
                      required={false}
                    />
                    <NumberField
                      name={values.mode === 'userDefined' ? 'blue.userMax' : 'blue.max'}
                      label="Max"
                      min={symbology.blue.min}
                      max={symbology.blue.max}
                      step={0.1}
                      disabled={values.mode !== 'userDefined'}
                      required={false}
                    />
                  </div>
                </div>
              </div>
            </fieldset>
            <div className="mt-4 flex items-center justify-between">
              <div className="w-28">
                <OutlineButton
                  type="button"
                  size="sm"
                  onClick={() =>
                    saveSymbology(
                      values,
                      symbologySettingsDispatch,
                      activeProject.id,
                      activeDataProduct,
                      activeDataProductDispatch
                    )
                  }
                >
                  Save
                </OutlineButton>
              </div>
              <div className="w-28">
                <Button size="sm" onClick={() => setOpen(true)}>
                  Share
                </Button>
                <Modal open={open} setOpen={setOpen}>
                  <ShareControls
                    currentAccess={activeDataProduct.access}
                    dataProduct={activeDataProduct}
                    projectID={activeProject.id}
                    symbologySettings={symbologySettings}
                  />
                </Modal>
              </div>
              <div className="w-28">
                <Button type="submit" size="sm">
                  Apply
                </Button>
              </div>
            </div>
          </Form>
        )}
      </Formik>
    );
  } else {
    return null;
  }
}

interface SymbologyControls {
  dataProductType: string;
}

export default function SymbologyControls({ dataProductType }: SymbologyControls) {
  const [open, setOpen] = useState(false);
  if (dataProductType === 'ortho')
    return <OrthoSymbologyControls open={open} setOpen={setOpen} />;
  if (dataProductType === 'dsm')
    return <DSMSymbologyControls open={open} setOpen={setOpen} />;
  return null;
}
