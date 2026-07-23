type BlendingModeType = 'average' | 'disabled' | 'min' | 'max' | 'mosaic';
type CameraType = 'single' | 'multi';
type FilterMode =
  | 'no_filtering'
  | 'mild_filtering'
  | 'moderate_filtering'
  | 'aggressive_filtering';
type QualityType = 'low' | 'medium' | 'high';

export interface MetashapeSettings {
  alignQuality: QualityType;
  backend: 'metashape';
  blendingMode: BlendingModeType;
  buildDepthQuality: QualityType;
  buildDepthFilterMode: FilterMode;
  camera: CameraType;
  cullFaces: boolean;
  disclaimer: boolean;
  exportDEM: boolean;
  exportDEMResolution: number;
  exportOrtho: boolean;
  exportOrthoResolution: number;
  exportPointCloud: boolean;
  fillHoles: boolean;
  ghostingFilter: boolean;
  keyPoint: number;
  refineSeamlines: boolean;
  resolution: number;
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
  failed?: boolean;
  initialCheck: boolean;
  jobId: string;
  progress: number;
  rawDataId: string;
};

export type JobStatus = 'WAITING' | 'INPROGRESS' | 'SUCCESS' | 'FAILED';
export type JobState = 'PENDING' | 'STARTED' | 'COMPLETED';

export type ImageProcessingBackend = 'metashape' | 'odm';

export type ProcessingJobExtra = {
  backend?: ImageProcessingBackend;
  settings?: Record<string, string | number | boolean>;
  batch_id?: string;
  detail?: string;
  progress?: number;
  report?: string;
};

export type ProcessingJob = {
  id: string;
  data_product_id: string | null;
  raw_data_id: string;
  name: string;
  state: JobState;
  status: JobStatus;
  start_time: string;
  end_time: string | null;
  extra: ProcessingJobExtra | null;
};

export type RawDataProps = {
  id: string;
  status: JobStatus | null;
  original_filename: string;
  report?: string;
  url: string;
};

export type RawDataImageProcessingFormProps = {
  onSubmitJob: (settings: MetashapeSettings | ODMSettings) => void;
  toggleModal: () => void;
};
