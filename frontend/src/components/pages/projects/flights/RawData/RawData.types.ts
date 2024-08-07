export type ImageProcessingJobProps = {
  initialCheck: boolean;
  jobId: string;
  progress: number;
  rawDataId: string;
};

export type RawDataProps = {
  id: string;
  initial_processing_status: string;
  original_filename: string;
  url: string;
};
