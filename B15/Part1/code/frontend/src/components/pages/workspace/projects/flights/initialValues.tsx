import { Flight } from '../Project';

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
  { label: 'Thermal', value: 'Thermal' },
  { label: 'Hyperspectral', value: 'Hyperspectral' },
  { label: 'Other', value: 'Other' },
];

const initialValues = {
  name: '',
  acquisitionDate: '',
  altitude: 120,
  sideOverlap: 60,
  forwardOverlap: 75,
  sensor: SENSOR_OPTIONS[0].value,
  platform: PLATFORM_OPTIONS[0].value,
  platformOther: '',
  pilotId: '',
};

const getPlatform = (platform: string): string => {
  const platformVals = PLATFORM_OPTIONS.map(({ value }) => value);
  if (platformVals.includes(platform)) {
    return platform;
  } else {
    // platform value entered in "Other" field
    return 'Other';
  }
};

export function getInitialValues(flight: Flight | null) {
  if (flight) {
    return {
      name: flight.name ? flight.name : '',
      acquisitionDate: flight.acquisition_date,
      altitude: flight.altitude,
      sideOverlap: flight.side_overlap,
      forwardOverlap: flight.forward_overlap,
      sensor: flight.sensor,
      platform: getPlatform(flight.platform),
      platformOther:
        getPlatform(flight.platform).toLowerCase() === 'other'
          ? flight.platform
          : '',
      pilotId: '',
    };
  } else {
    return initialValues;
  }
}

export default initialValues;
