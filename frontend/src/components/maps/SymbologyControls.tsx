// http://localhost/cog/tiles/WebMercatorQuad/19/135564/197664@1x?url=https%3A%2F%2Fhub.digitalforestry.org%2Fpurdue_campus%2Fpurdue-push-20231028-p1-ortho.tif&bidx=1&bidx=2&bidx=4
import { Field, Formik, Form } from 'formik';

import { cmaps } from './cmaps';
import { Button, OutlineButton } from '../Buttons';
import { NumberField, SelectField } from '../InputFields';
import { useMapContext } from './MapContext';

const round = (n: number, digits: number): number => parseFloat(n.toFixed(digits));

function DSMSymbologyControls() {
  const { activeDataProduct, symbologySettings, symbologySettingsDispatch } =
    useMapContext();
  const stats = activeDataProduct?.stac_properties.raster[0].stats;

  return (
    <Formik
      initialValues={symbologySettings}
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
              aria-labelledby="minMaxGroup"
            >
              <label className="block text-sm text-gray-600 font-bold pt-2 pb-1">
                <Field type="radio" name="minMax" value="minMax" />
                <span className="ml-2">Min/Max</span>
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
}

function OrthoSymbologyControls() {
  const { activeDataProduct, symbologySettingsDispatch } = useMapContext();
  const bandOptions = activeDataProduct?.stac_properties.eo.map((band, idx) => ({
    label: band.name,
    value: idx + 1,
  }));
  const initialValues = activeDataProduct?.user_style
    ? { ...activeDataProduct.user_style }
    : { redBand: 3, greenBand: 2, blueBand: 1 };
  if (bandOptions) {
    return (
      <Formik
        initialValues={initialValues}
        onSubmit={(values) => {
          symbologySettingsDispatch({
            type: 'update',
            payload: values,
          });
        }}
      >
        {({}) => (
          <Form>
            <fieldset className="border border-solid border-slate-300 p-3">
              <legend>RGB Properties</legend>
              <div className="grid grid-rows-2 gap-4">
                <div className="grid grid-cols-4 gap-4">
                  <SelectField name="redBand" label="Red" options={bandOptions} />
                  <SelectField name="greenBand" label="Green" options={bandOptions} />
                  <SelectField name="blueBand" label="Blue" options={bandOptions} />
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
