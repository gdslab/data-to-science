export const customSliderStyles = {
  '& .MuiSlider-thumb': {
    width: '22px',
    height: '22px',
    backgroundColor: '#484848',
    border: '1px solid #000000',
  },
  '& .MuiSlider-thumbColorPrimary': {
    '&:hover, &.Mui-focusVisible': {
      boxShadow: '0 0 0 8px rgba(72, 72, 72, 0.16)',
    },
    '&.Mui-active': {
      boxShadow: '0 0 0 12px rgba(72, 72, 72, 0.16)', // Larger shadow when active
    },
  },
  '& .MuiSlider-markLabel': {
    fontSize: '10px',
    color: 'black',
    left: '30px',
  },
  '& .MuiSlider-track': {
    backgroundColor: '#B8B8B8',
    height: '8px',
    color: '#000000',
    borderRadius: '0px',
  },
  '& .MuiSlider-rail': {
    backgroundColor: '#B8B8B8',
    height: '8px',
    border: '1px solid #000000',
    borderRadius: '0px',
  },
};
