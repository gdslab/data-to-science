import axios, { AxiosResponse } from 'axios';
import { Field, Formik, Form } from 'formik';
import { useEffect, useState } from 'react';

import { Button, OutlineButton } from '../Buttons';
import { SymbologySettings, useMapContext } from './MapContext';
import { NumberField, SelectField } from '../InputFields';
import HintText from '../HintText';

const colorRampOptions = [
  { label: 'Blue Purple', value: 'bupu' },
  { label: 'Spectral', value: 'spectral' },
  { label: 'Turbo', value: 'turbo' },
  { label: 'Yellow Green Blue', value: 'ylgnbu' },
  { label: 'Yellow Orange Red', value: 'ylorrd' },
];

const round = (n: number, digits: number): number => parseFloat(n.toFixed(digits));

export default function SymbologyControl() {
  const [initialValues, setInitialValues] = useState<SymbologySettings | null>(null);
  const {
    activeDataProduct,
    activeProject,
    geoRasterIdDispatch,
    symbologySettings,
    symbologySettingsDispatch,
  } = useMapContext();

  const stats = activeDataProduct?.band_info.bands[0].stats;

  useEffect(() => {
    symbologySettingsDispatch({
      type: 'update',
      payload: {
        ...symbologySettings,
        min: stats ? round(stats.minimum, 1) : symbologySettings.min,
        max: stats ? round(stats.maximum, 1) : symbologySettings.max,
        userMin: stats ? round(stats.minimum, 1) : symbologySettings.min,
        userMax: stats ? round(stats.maximum, 1) : symbologySettings.max,
      },
    });
    setInitialValues(symbologySettings);
  }, []);

  if (initialValues) {
    return (
      <div className="p-2.5 w-96">
        <Formik
          initialValues={symbologySettings}
          onSubmit={(values) => {
            geoRasterIdDispatch({ type: 'create' });
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
                  <SelectField
                    name="colorRamp"
                    label="Color Ramp"
                    options={colorRampOptions}
                  />
                </fieldset>
              </div>
              <fieldset className="border border-solid border-slate-300 p-3">
                <legend className="block text-sm text-gray-400 font-bold pt-2 pb-1">
                  Min / Max Value Settings
                </legend>
                <div
                  className="w-full flex flex-wrap gap-3 mb-4"
                  role="group"
                  aria-labelledby="minMaxGroup"
                >
                  <label className="block text-sm text-gray-600 font-bold pt-2 pb-1">
                    <Field type="radio" name="minMax" value="minMax" />
                    <span className="ml-2">Min/Max</span>
                  </label>
                  <label className="block text-sm text-gray-600 font-bold pt-2 pb-1">
                    <Field type="radio" name="minMax" value="countCut" />
                    <span className="ml-2">Cumulative count cut</span>
                  </label>
                  <label className="block text-sm text-gray-600 font-bold pt-2 pb-1">
                    <Field type="radio" name="minMax" value="userDefined" />
                    <span className="ml-2">User defined</span>
                  </label>
                  <label className="block text-sm text-gray-600 font-bold pt-2 pb-1">
                    <Field type="radio" name="minMax" value="meanStdDev" />
                    <span className="ml-2">Mean +/- Std. Dev.</span>
                  </label>
                </div>
                {values.minMax === 'minMax' ? (
                  <div className="w-full flex gap-4">
                    <div className="w-1/3">
                      <NumberField
                        name="min"
                        label="Min"
                        min={stats ? round(stats.minimum, 1) : 0}
                        max={stats ? round(stats.maximum, 1) : 9999}
                        step={0.1}
                        disabled
                      />
                    </div>
                    <div className="w-1/3">
                      <NumberField
                        name="max"
                        label="Max"
                        min={stats ? round(stats.minimum, 1) : 0}
                        max={stats ? round(stats.maximum, 1) : 9999}
                        step={0.1}
                        disabled
                      />
                    </div>
                  </div>
                ) : null}
                {values.minMax === 'userDefined' ? (
                  <div className="w-full flex gap-4">
                    <div className="w-1/3">
                      <NumberField
                        name="userMin"
                        label="Min"
                        min={stats ? round(stats.minimum, 1) : 0}
                        max={stats ? round(stats.maximum, 1) : 9999}
                        step={0.1}
                        required={false}
                      />
                    </div>
                    <div className="w-1/3">
                      <NumberField
                        name="userMax"
                        label="Max"
                        min={stats ? round(stats.minimum, 1) : 0}
                        max={stats ? round(stats.maximum, 1) : 9999}
                        step={0.1}
                        required={false}
                      />
                    </div>
                  </div>
                ) : null}
                {values.minMax === 'countCut' ? (
                  <div className="w-full flex gap-4">
                    <div className="w-1/3">
                      <NumberField
                        name="minCut"
                        label="Lowest"
                        min={0}
                        max={100}
                        step={0.1}
                        required={false}
                      />
                    </div>
                    <div className="w-1/3">
                      <NumberField
                        name="maxCut"
                        label="Highest"
                        min={0}
                        max={100}
                        step={0.1}
                        required={false}
                      />
                    </div>
                  </div>
                ) : null}
                {values.minMax === 'meanStdDev' ? (
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
              <div className="mt-4 w-1/2">
                <OutlineButton type="submit" size="sm">
                  Apply Symbology
                </OutlineButton>
              </div>
            </Form>
          )}
        </Formik>
        <div className="mt-4">
          <div className="mb-4">
            <HintText>
              Load default symbology settings or save current settings.
            </HintText>
          </div>
          <div className="flex items-center justify-between">
            <div className="w-28">
              <Button size="sm">Load Default</Button>
            </div>
            <div className="w-28">
              <Button
                size="sm"
                onClick={async () => {
                  if (activeProject && activeDataProduct) {
                    try {
                      let response: null | AxiosResponse = null;
                      if (!activeDataProduct.user_style) {
                        response = await axios.post(
                          `/api/v1/projects/${activeProject.id}/flights/${activeDataProduct.flight_id}/data_products/${activeDataProduct.id}/style`,
                          { settings: symbologySettings }
                        );
                      } else {
                        response = await axios.put(
                          `/api/v1/projects/${activeProject.id}/flights/${activeDataProduct.flight_id}/data_products/${activeDataProduct.id}/style`,
                          { settings: symbologySettings }
                        );
                      }
                      if (response) {
                        // do something
                      }
                    } catch (err) {
                      console.error(err);
                    }
                  }
                }}
              >
                Save
              </Button>
            </div>
          </div>
        </div>
      </div>
    );
  } else {
    return null;
  }
}
