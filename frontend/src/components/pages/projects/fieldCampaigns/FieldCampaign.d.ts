export type ActiveStep = {
  activeStep: number;
  handleSubmit: (extra: any) => (values: any, actions: any) => Promise<void>;
  isSubmitting: boolean;
  setActiveStep: React.Dispatch<React.SetStateAction<number>>;
};

export type FieldCampaignResponse = {
  title: string;
  id: string;
  lead_id: string;
  project_id: string;
};

export type Measurement = {
  name: string;
  units: string;
  timepoints: {
    numberOfSamples: number;
    sampleNames: string[];
    timepointIdentifier: string;
    columns: string[];
  }[];
};

type Treatment = {
  data: string[];
  filenames: string[];
  columns: {
    name: string;
    selected: boolean;
  }[];
  name: string;
};

export type FieldCampaignInitialValues = {
  newColumns: {
    name: string;
    fill: string;
    placeholder?: string;
  }[];
  measurements: Measurement[];
  treatments: Treatment[];
};

export type TemplateInput = {
  [key: string]: unknown;
};

export type TemplateUpload = {
  id: string;
  setCsvErrors: React.Dispatch<
    React.SetStateAction<Papa.ParseError[] | Omit<Papa.ParseError, 'code'>[]>
  >;
};
