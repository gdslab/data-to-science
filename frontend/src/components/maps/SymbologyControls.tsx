import axios from 'axios';
import { Field, Formik, Form } from 'formik';
import { useState } from 'react';

import { useMapContext } from './MapContext';

import { Button } from '../Buttons';
import { DataProduct } from '../pages/workspace/projects/Project';
import { NumberField, SelectField } from '../InputFields';
import {
  DSMSymbologySettings,
  OrthoSymbologySettings,
  SymbologySettings,
  SymbologySettingsAction,
} from './Maps';
import Modal from '../Modal';
import OpacitySlider from './OpacitySlider';
import { Project } from '../pages/workspace/ProjectList';
import ShareControls from './ShareControls';

import { cmaps } from './cmaps';

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

function ShareDataProduct({
  dataProduct,
  project,
  symbologySettings,
}: {
  dataProduct: DataProduct;
  project: Project;
  symbologySettings: SymbologySettings;
}) {
  const [open, setOpen] = useState(false);
  return (
    <div>
      <Button type="button" size="sm" icon="share2" onClick={() => setOpen(true)}>
        Share
      </Button>
      <Modal open={open} setOpen={setOpen}>
        <ShareControls
          dataProduct={dataProduct}
          project={project}
          symbologySettings={symbologySettings}
        />
      </Modal>
    </div>
  );
}

function DSMSymbologyControls() {
  const {
    activeDataProduct,
    activeDataProductDispatch,
    activeProject,
    symbologySettings,
    symbologySettingsDispatch,
  } = useMapContext();
  if (activeProject && activeDataProduct) {
    const symbology = symbologySettings as DSMSymbologySettings;
    const step: number =
      activeDataProduct.stac_properties.raster[0].data_type == 'unit8' ? 1 : 0.001;
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
        {({ values, setFieldTouched, setFieldValue, submitForm }) => (
          <Form>
            <div className="w-full mb-4">
              <fieldset className=" flex flex-col gap-4 border border-solid border-slate-300 p-3">
                <legend className="block text-sm text-gray-400 font-bold pt-2 pb-1">
                  Color Properties
                </legend>
                <SelectField
                  name="colorRamp"
                  label="Color Ramp"
                  options={cmaps}
                  onChange={(e) => {
                    setFieldValue('colorRamp', e.target.value);
                    setFieldTouched('colorRamp', true);
                    submitForm();
                  }}
                />
                <OpacitySlider
                  currentValue={values.opacity}
                  onChange={(_: Event, newValue: number | number[]) => {
                    setFieldValue('opacity', newValue);
                    setFieldTouched('opacity', true);
                    submitForm();
                  }}
                />
              </fieldset>
            </div>
            <fieldset className="border border-solid border-slate-300 p-3">
              <legend className="block text-sm text-gray-400 font-bold pt-2 pb-1">
                Min / Max Value Settings
              </legend>
              <div
                className="w-full flex flex-wrap justify-between gap-1.5"
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
                      step={step}
                      disabled
                    />
                  </div>
                  <div className="w-1/3">
                    <NumberField
                      name="max"
                      label="Max"
                      min={symbology.min}
                      max={symbology.max}
                      step={step}
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
                      step={step}
                      required={false}
                    />
                  </div>
                  <div className="w-1/3">
                    <NumberField
                      name="userMax"
                      label="Max"
                      step={step}
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
              <div className="w-full flex justify-end mt-4">
                <Button type="submit" size="xs">
                  Apply Changes
                </Button>
              </div>
            </fieldset>
            <div className="mt-4 w-full flex items-center justify-between">
              <div className="w-36">
                <ShareDataProduct
                  dataProduct={activeDataProduct}
                  project={activeProject}
                  symbologySettings={symbologySettings}
                />
              </div>
              <div className="w-36">
                <Button
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
                  Save Changes
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

function OrthoSymbologyControls() {
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
    const step: number =
      activeDataProduct.stac_properties.raster[0].data_type == 'unit8' ? 1 : 0.1;
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
        {({ values, setFieldTouched, setFieldValue, submitForm }) => (
          <Form>
            <fieldset className="border border-solid border-slate-300 p-3">
              <legend className="block text-sm text-gray-400 font-bold pt-2 pb-1">
                RGB Properties
              </legend>
              <div
                className="w-full flex flex-wrap justify-between gap-1.5"
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
              <div className="mt-4 flex flex-col gap-4">
                <div className="grid grid-cols-3 gap-4">
                  <div className="grid grid-rows-3 gap-1.5 border-2 border-dotted border-red-500 rounded-md p-1.5">
                    <SelectField name="red.idx" label="Red" options={bandOptions} />
                    <NumberField
                      name={values.mode === 'userDefined' ? 'red.userMin' : 'red.min'}
                      label="Min"
                      min={
                        values.mode === 'userDefined' ? undefined : symbology.red.min
                      }
                      max={
                        values.mode === 'userDefined' ? undefined : symbology.red.max
                      }
                      step={step}
                      disabled={values.mode !== 'userDefined'}
                      required={false}
                    />
                    <NumberField
                      name={values.mode === 'userDefined' ? 'red.userMax' : 'red.max'}
                      label="Max"
                      min={
                        values.mode === 'userDefined' ? undefined : symbology.red.min
                      }
                      max={
                        values.mode === 'userDefined' ? undefined : symbology.red.max
                      }
                      step={step}
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
                      min={
                        values.mode === 'userDefined' ? undefined : symbology.green.min
                      }
                      max={
                        values.mode === 'userDefined' ? undefined : symbology.green.max
                      }
                      step={step}
                      disabled={values.mode !== 'userDefined'}
                      required={false}
                    />
                    <NumberField
                      name={
                        values.mode === 'userDefined' ? 'green.userMax' : 'green.max'
                      }
                      label="Max"
                      min={
                        values.mode === 'userDefined' ? undefined : symbology.green.min
                      }
                      max={
                        values.mode === 'userDefined' ? undefined : symbology.green.max
                      }
                      step={step}
                      disabled={values.mode !== 'userDefined'}
                      required={false}
                    />
                  </div>
                  <div className="grid grid-rows-3 gap-1.5 border-2 border-dotted border-blue-500 rounded-md p-1.5">
                    <SelectField name="blue.idx" label="Blue" options={bandOptions} />
                    <NumberField
                      name={values.mode === 'userDefined' ? 'blue.userMin' : 'blue.min'}
                      label="Min"
                      min={
                        values.mode === 'userDefined' ? undefined : symbology.blue.min
                      }
                      max={
                        values.mode === 'userDefined' ? undefined : symbology.blue.max
                      }
                      step={0.1}
                      disabled={values.mode !== 'userDefined'}
                      required={false}
                    />
                    <NumberField
                      name={values.mode === 'userDefined' ? 'blue.userMax' : 'blue.max'}
                      label="Max"
                      min={
                        values.mode === 'userDefined' ? undefined : symbology.blue.min
                      }
                      max={
                        values.mode === 'userDefined' ? undefined : symbology.blue.max
                      }
                      step={0.1}
                      disabled={values.mode !== 'userDefined'}
                      required={false}
                    />
                  </div>
                </div>
                <OpacitySlider
                  currentValue={values.opacity}
                  onChange={(_: Event, newValue: number | number[]) => {
                    setFieldValue('opacity', newValue);
                    setFieldTouched('opacity', true);
                    submitForm();
                  }}
                />
              </div>
              <div className="w-full flex justify-end mt-4">
                <Button type="submit" size="xs">
                  Apply Changes
                </Button>
              </div>
            </fieldset>
            <div className="mt-4 w-full flex items-center justify-between">
              <div className="w-36">
                <ShareDataProduct
                  dataProduct={activeDataProduct}
                  project={activeProject}
                  symbologySettings={symbologySettings}
                />
              </div>
              <div className="w-36">
                <Button
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
                  Save Changes
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
  numOfBands: number;
}

export default function SymbologyControls({ numOfBands }: SymbologyControls) {
  if (numOfBands > 1) return <OrthoSymbologyControls />;
  if (numOfBands === 1) return <DSMSymbologyControls />;
  return null;
}
