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
