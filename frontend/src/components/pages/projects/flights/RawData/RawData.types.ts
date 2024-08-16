type CameraType = 'single' | 'multi';
type QualityType = 'low' | 'medium' | 'high';

export interface ImageProcessingSettings {
  alignQuality: QualityType;
  buildDepthQuality: QualityType;
  camera: CameraType;
  disclaimer: boolean;
  keyPoint: number;
  tiePoint: number;
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
  url: string;
};

export type RawDataImageProcessingFormProps = {
  onSubmitJob: (settings: ImageProcessingSettings) => void;
  toggleModal: () => void;
};
