import { DataProduct } from '../../pages/workspace/projects/Project';
import {
  MultibandSymbology,
  SingleBandSymbology,
  SymbologyMode,
  useRasterSymbologyContext,
} from '../RasterSymbologyContext';

type ModeRadioInputProps = {
  currentMode: 'minMax' | 'userDefined' | 'meanStdDev';
  label: string;
  value: 'minMax' | 'userDefined' | 'meanStdDev';
  onChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
};

function ModeRadioInput({
  currentMode,
  label,
  value,
  onChange,
}: ModeRadioInputProps) {
  return (
    <label className="block text-sm font-semibold pt-2 pb-1">
      <input
        type="radio"
        name="mode"
        value={value}
        checked={currentMode === value}
        onChange={onChange}
      />
      <span className="ml-2">{label}</span>
    </label>
  );
}

export default function RasterSymbologyModeRadioGroup({
  dataProduct,
}: {
  dataProduct: DataProduct;
}) {
  const { state, dispatch } = useRasterSymbologyContext();

  const symbology = state[dataProduct.id].symbology;

  // Early return if symbology is null
  if (!symbology) return null;

  const isSingleBandSymbology = (
    symbology: SingleBandSymbology | MultibandSymbology
  ): symbology is SingleBandSymbology => {
    return 'colorRamp' in symbology;
  };

  const isMultibandSymbology = (
    symbology: SingleBandSymbology | MultibandSymbology
  ): symbology is MultibandSymbology => {
    return 'red' in symbology;
  };

  const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const value = event.target.value as SymbologyMode;

    if (isSingleBandSymbology(symbology)) {
      const updatedSymbology: SingleBandSymbology = {
        ...symbology,
        mode: value,
      };
      dispatch({
        type: 'SET_SYMBOLOGY',
        rasterId: dataProduct.id,
        payload: updatedSymbology,
      });
    } else if (isMultibandSymbology(symbology)) {
      const updatedSymbology: MultibandSymbology = {
        ...symbology,
        mode: value,
      };
      dispatch({
        type: 'SET_SYMBOLOGY',
        rasterId: dataProduct.id,
        payload: updatedSymbology,
      });
    } else {
      console.error('Unknown symbology type');
    }
  };

  return (
    <div
      className="flex flex-wrap justify-between gap-1.5"
      role="group"
      aria-labelledby="modeGroup"
    >
      <ModeRadioInput
        currentMode={symbology.mode}
        label="Min/Max"
        value="minMax"
        onChange={handleInputChange}
      />
      <ModeRadioInput
        currentMode={symbology.mode}
        label="User defined"
        value="userDefined"
        onChange={handleInputChange}
      />
      <ModeRadioInput
        currentMode={symbology.mode}
        label="Mean +/- Std. Dev."
        value="meanStdDev"
        onChange={handleInputChange}
      />
    </div>
  );
}
