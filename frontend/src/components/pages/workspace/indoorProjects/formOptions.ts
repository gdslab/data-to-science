import {
  CameraOrientationOptions,
  PlottedByOptions,
  AccordingToOptions,
} from './IndoorProject';

const cameraOrientationOptions: CameraOrientationOptions = [
  { label: 'Top', value: 'top' },
  { label: 'Side', value: 'side' },
];

const plottedByOptions: PlottedByOptions = [
  { label: 'Groups', value: 'groups' },
  { label: 'Pots', value: 'pots' },
];

// Options for when "Groups" is selected
const groupsAccordingToOptions: AccordingToOptions = [
  { label: 'Treatment', value: 'treatment' },
  { label: 'Description', value: 'description' },
  { label: 'Treatment and Description', value: 'treatment_description' },
];

// Options for when "Pots" is selected - this will need to be populated dynamically
// For now, using placeholder values that should be replaced with actual pot IDs
const potsAccordingToOptions: AccordingToOptions = [
  { label: 'All', value: 'all' },
  // TODO: Replace with actual pot IDs from the data
  // { label: 'Pot 1', value: 'pot_1' },
  // { label: 'Pot 2', value: 'pot_2' },
  // etc.
];

export {
  cameraOrientationOptions,
  plottedByOptions,
  groupsAccordingToOptions,
  potsAccordingToOptions,
};
