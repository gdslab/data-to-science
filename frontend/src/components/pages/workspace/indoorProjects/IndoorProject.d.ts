export type IndoorProjectAPIResponse = {
  id: string;
  title: string;
  description: string;
  start_date?: Date;
  end_date?: Date;
};

export type IndoorProjectUploadInputProps = {
  indoorProjectId: string;
};
