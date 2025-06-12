import { MetashapeSettings } from '../../RawData.types';

const defaultValues: MetashapeSettings = {
  alignQuality: 'medium',
  backend: 'metashape',
  blendingMode: 'mosaic',
  buildDepthQuality: 'medium',
  camera: 'single',
  disclaimer: false,
  fillHoles: true,
  ghostingFilter: false,
  cullFaces: false,
  refineSeamlines: false,
  resolution: 0,
  keyPoint: 40000,
  tiePoint: 4000,
};

export default defaultValues;
