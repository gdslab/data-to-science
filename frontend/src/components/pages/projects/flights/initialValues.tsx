export const PLATFORM_OPTIONS = [
  { label: 'Phantom 4', value: 'Phantom_4' },
  { label: 'M300', value: 'M300' },
  { label: 'M350', value: 'M350' },
  { label: 'Other', value: 'Other' },
];
export const SENSOR_OPTIONS = [
  { label: 'RGB', value: 'RGB' },
  { label: 'Multispectral', value: 'Multispectral' },
  { label: 'LiDAR', value: 'LiDAR' },
  { label: 'Other', value: 'Other' },
];

const initialValues = {
  acquisitionDate: '',
  altitude: 120,
  sideOverlap: 60,
  forwardOverlap: 75,
  sensor: SENSOR_OPTIONS[0].value,
  platform: PLATFORM_OPTIONS[0].value,
  pilotId: '',
  //   pilot: "" // List of team members with access to the project?
  // If no team associated with the project, pilot = logged in user?
};

export default initialValues;