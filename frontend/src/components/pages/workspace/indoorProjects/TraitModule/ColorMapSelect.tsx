import Select, { SingleValue } from 'react-select';

import { ColorMapOption } from '../../../../maps/RasterSymbologySettings/cmaps';
import { nivoColorSchemeMap } from './nivoColorSchemeMap';
import {
  nivoSequentialColors,
  nivoColorMapGroupedOptions,
  nivoCategoricalColors,
} from '../utils';

type ColorMapSelectProps = {
  colorPreviewCount?: number;
  setColorOption: React.Dispatch<React.SetStateAction<string>>;
  defaultValue?: ColorMapOption;
  categoricalOnly?: boolean;
};

export default function ColorMapSelect({
  setColorOption,
  colorPreviewCount,
  defaultValue,
  categoricalOnly = false,
}: ColorMapSelectProps) {
  const handleChange = (colorOption: SingleValue<ColorMapOption>) => {
    if (colorOption) {
      setColorOption(colorOption.value);
    }
  };

  const formatOptionLabel = ({ value, label }) => {
    // Look up the colors for this scheme (or default to an empty array)
    const colors = nivoColorSchemeMap[value] || [];
    return (
      <div style={{ display: 'flex', alignItems: 'center' }}>
        {/* Reserve a fixed-width container for the label */}
        <div
          style={{
            width: '150px',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
          }}
        >
          {label}
        </div>
        {colors.length > 0 && (
          <div style={{ display: 'flex', marginLeft: '8px' }}>
            {colors
              .slice(0, colorPreviewCount || colors.length)
              .map((color, index) => (
                <div
                  key={index}
                  style={{
                    width: '15px',
                    height: '15px',
                    backgroundColor: color,
                    marginRight: '2px',
                  }}
                />
              ))}
          </div>
        )}
      </div>
    );
  };

  // Determine which options to use based on categoricalOnly prop
  const options = categoricalOnly
    ? [{ label: 'Categorical Colors', options: nivoCategoricalColors }]
    : nivoColorMapGroupedOptions;

  return (
    <fieldset>
      <legend>Color scheme:</legend>
      <Select<ColorMapOption>
        styles={{
          input: (base) => ({
            ...base,
            'input:focus': {
              boxShadow: 'none',
            },
          }),
        }}
        theme={(theme) => ({
          ...theme,
          colors: {
            ...theme.colors,
            primary: '#3d5a80',
            primary25: '#e2e8f0',
          },
        })}
        isSearchable
        defaultValue={defaultValue || nivoSequentialColors[1]}
        options={options}
        onChange={handleChange}
        formatOptionLabel={formatOptionLabel}
        menuPlacement="top"
      />
    </fieldset>
  );
}
