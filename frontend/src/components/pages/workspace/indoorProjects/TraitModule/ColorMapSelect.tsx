import Select, { SingleValue } from 'react-select';

import { ColorMapOption } from '../../../../maps/RasterSymbologySettings/cmaps';
import { nivoColorSchemeMap } from './nivoColorSchemeMap';
import { nivoSequentialColors, nivoColorMapGroupedOptions } from '../utils';

type ColorMapSelectProps = {
  colorPreviewCount?: number;
  setColorOption: React.Dispatch<React.SetStateAction<string>>;
};

export default function ColorMapSelect({
  setColorOption,
  colorPreviewCount,
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
        defaultValue={nivoSequentialColors[1]}
        options={nivoColorMapGroupedOptions}
        onChange={handleChange}
        formatOptionLabel={formatOptionLabel}
        menuPlacement="top"
      />
    </fieldset>
  );
}
