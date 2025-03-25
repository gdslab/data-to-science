import { CameraOrientationOptions, GroupByOptions } from './IndoorProject';

const cameraOrientationOptions: CameraOrientationOptions = [
  { label: 'Top', value: 'top' },
  { label: 'Side', value: 'side' },
];

const groupByOptions: GroupByOptions = [
  { label: 'Treatment', value: 'treatment' },
  { label: 'Description', value: 'description' },
  { label: 'Treatment Description', value: 'treatment_description' },
  { label: 'All Pots', value: 'all_pots' },
  { label: 'Single Pot', value: 'single_pot' },
];

export { cameraOrientationOptions, groupByOptions };
