import { DataProduct } from '../../pages/projects/Project';
import {
  MultibandSymbology,
  SingleBandSymbology,
  SymbologyMode,
  useRasterSymbologyContext,
} from '../RasterSymbologyContext';

export default function RasterSymbologyModeRadioGroup({
  dataProduct,
}: {
  dataProduct: DataProduct;
}) {
  const { state, dispatch } = useRasterSymbologyContext();

  const symbology = state[dataProduct.id].symbology;

  const isSingleBandSymbology = (symbology: any): symbology is SingleBandSymbology => {
    return 'colorRamp' in symbology;
  };

  const isMultibandSymbology = (symbology: any): symbology is MultibandSymbology => {
    return 'red' in symbology;
  };

  const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const value = event.target.value as SymbologyMode;

    if (isSingleBandSymbology(symbology)) {
      const updatedSymbology: SingleBandSymbology = { ...symbology, mode: value };
      dispatch({
        type: 'SET_SYMBOLOGY',
        rasterId: dataProduct.id,
        payload: updatedSymbology,
      });
    } else if (isMultibandSymbology(symbology)) {
      const updatedSymbology: MultibandSymbology = { ...symbology, mode: value };
      dispatch({
        type: 'SET_SYMBOLOGY',
        rasterId: dataProduct.id,
        payload: updatedSymbology,
      });
    } else {
      console.error('Unknown symbology type');
    }
  };

  const ModeRadioInput = ({
    currentMode,
    label,
    value,
  }: {
    currentMode: 'minMax' | 'userDefined' | 'meanStdDev';
    label: string;
    value: 'minMax' | 'userDefined' | 'meanStdDev';
  }) => (
    <label className="block text-sm font-semibold pt-2 pb-1">
      <input
        type="radio"
        name="mode"
        value={value}
        checked={currentMode === value}
        onChange={handleInputChange}
      />
      <span className="ml-2">{label}</span>
    </label>
  );

  if (!symbology) return;

  return (
    <div
      className="flex flex-wrap justify-between gap-1.5"
      role="group"
      aria-labelledby="modeGroup"
    >
      <ModeRadioInput currentMode={symbology.mode} label="Min/Max" value="minMax" />
      <ModeRadioInput
        currentMode={symbology.mode}
        label="User defined"
        value="userDefined"
      />
      <ModeRadioInput
        currentMode={symbology.mode}
        label="Mean +/- Std. Dev."
        value="meanStdDev"
      />
    </div>
  );
}
