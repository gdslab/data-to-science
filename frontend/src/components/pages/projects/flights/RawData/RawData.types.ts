type BlendingModeType = 'average' | 'disabled' | 'min' | 'max' | 'mosaic';
type CameraType = 'single' | 'multi';
type QualityType = 'low' | 'medium' | 'high';

export interface MetashapeSettings {
  alignQuality: QualityType;
  backend: 'metashape';
  blendingMode: BlendingModeType;
  buildDepthQuality: QualityType;
  camera: CameraType;
  disclaimer: boolean;
  keyPoint: number;
  tiePoint: number;
}

type PCQualityType = 'lowest' | 'low' | 'medium' | 'high' | 'ultra';

export interface ODMSettings {
  backend: 'odm';
  disclaimer: boolean;
  orthoResolution: number;
  pcQuality: PCQualityType;
}

export type ImageProcessingJobProps = {
  initialCheck: boolean;
  jobId: string;
  progress: number;
  rawDataId: string;
};

export type RawDataProps = {
  id: string;
  status: string;
  original_filename: string;
  report?: string;
  url: string;
};

export type RawDataImageProcessingFormProps = {
  onSubmitJob: (settings: MetashapeSettings | ODMSettings) => void;
  toggleModal: () => void;
};
