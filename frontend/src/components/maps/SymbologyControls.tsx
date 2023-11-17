import { Field, Formik, Form } from 'formik';

import { cmaps } from './cmaps';
import { Button, OutlineButton } from '../Buttons';
import { NumberField, SelectField } from '../InputFields';
import {
  DSMSymbologySettings,
  OrthoSymbologySettings,
  useMapContext,
} from './MapContext';

/**
 * Determine number of decimal places for input number field's step attribute.
 * @param {number} n Integer or floating point number.
 * @returns {string} Numeric string of step value.
 */
const findStep = (n: number): number =>
  parseFloat('0.' + ''.padStart(n.toString().split('.')[1].length - 1, '0') + '1');

function DSMSymbologyControls() {
  const { activeDataProduct, symbologySettings, symbologySettingsDispatch } =
    useMapContext();

  if (activeDataProduct && symbologySettings) {
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
        {({ handleReset, values }) => (
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
              <div className="w-48">
                <OutlineButton type="button" size="sm" onClick={() => handleReset()}>
                  Reset
                </OutlineButton>
              </div>
              <div className="w-48">
                <Button type="submit" size="sm">
                  Apply Symbology
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
  const { activeDataProduct, symbologySettings, symbologySettingsDispatch } =
    useMapContext();

  const symbology = symbologySettings as OrthoSymbologySettings;
  if (activeDataProduct && symbology) {
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
        {() => (
          <Form>
            <fieldset className="border border-solid border-slate-300 p-3">
              <legend>RGB Properties</legend>
              <div className="flex flex-col gap-4">
                <div className="grid grid-cols-3 gap-4">
                  <div className="grid grid-rows-3 gap-1.5 border border-red-500 rounded p-1.5">
                    <SelectField name="red.idx" label="Red" options={bandOptions} />
                    <NumberField
                      name="red.min"
                      label="Min"
                      min={0}
                      max={255}
                      step={0.1}
                      required={false}
                    />
                    <NumberField
                      name="red.max"
                      label="Max"
                      min={symbology.red.min}
                      max={symbology.red.max}
                      step={
                        activeDataProduct.stac_properties.raster[0].data_type == 'unit8'
                          ? 1
                          : 0.1
                      }
                      required={false}
                    />
                  </div>
                  <div className="grid grid-rows-3 gap-1.5 border border-green-500 rounded p-1.5">
                    <SelectField name="green.idx" label="Green" options={bandOptions} />
                    <NumberField
                      name="green.min"
                      label="Min"
                      min={symbology.green.min}
                      max={symbology.green.max}
                      step={
                        activeDataProduct.stac_properties.raster[0].data_type == 'unit8'
                          ? 1
                          : 0.1
                      }
                      required={false}
                    />
                    <NumberField
                      name="green.max"
                      label="Max"
                      min={symbology.green.min}
                      max={symbology.green.max}
                      step={
                        activeDataProduct.stac_properties.raster[0].data_type == 'unit8'
                          ? 1
                          : 0.1
                      }
                      required={false}
                    />
                  </div>
                  <div className="grid grid-rows-3 gap-1.5 border border-blue-500 rounded p-1.5">
                    <SelectField name="blue.idx" label="Blue" options={bandOptions} />
                    <NumberField
                      name="blue.min"
                      label="Min"
                      min={symbology.blue.min}
                      max={symbology.blue.max}
                      step={0.1}
                      required={false}
                    />
                    <NumberField
                      name="blue.max"
                      label="Max"
                      min={symbology.blue.min}
                      max={symbology.blue.max}
                      step={0.1}
                      required={false}
                    />
                  </div>
                </div>
                <div className="w-1/2">
                  <OutlineButton type="submit" size="sm">
                    Apply Symbology
                  </OutlineButton>
                </div>
              </div>
            </fieldset>
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
  if (dataProductType === 'ortho') return <OrthoSymbologyControls />;
  if (dataProductType === 'dsm') return <DSMSymbologyControls />;
  return null;
}
