// Types for indoor project API responses
export type IndoorProjectAPIResponse = {
  id: string;
  title: string;
  description: string;
  start_date?: Date;
  end_date?: Date;
  team_id?: string | null;
};

export interface IndoorProjectMember {
  id: string;
  full_name: string;
  email: string;
  role: string;
  profile_url: string | null;
  member_id: string;
}

export type IndoorProjectDataAPIResponse = {
  id: string;
  original_filename: string;
  stored_filename: string;
  file_path: string;
  file_size: number;
  file_type: string;
  treatment?: string;
  is_initial_processing_completed: boolean;
  upload_date: Date;
};

export type NumericColumns = {
  top: string[];
  side: string[];
};

export type IndoorProjectDataSpreadsheetAPIResponse = {
  records: {
    [key: number]: IndoorProjectDataPlantAPIResponse;
  };
  summary: {
    id?: string;
    exp_id: number[];
    treatment: string[];
    species_name: string[];
    entry: string[];
    pot_barcode: number[];
    planting_date: Date;
    pottype: string[];
    ct_configuration: string[];
    variety: string[];
    year: number[];
    pi: string[];
  };
  numeric_columns: NumericColumns;
};

export type IndoorProjectDataSpreadsheetTop = {
  filename: string;
  images: string[];
  exp_id: number;
  pot_barcode: number;
  variety: string;
  treatment: string;
  scan_time: string;
  scan_date: string;
  dfp: number;
  angle: number;
  surface: number;
  convex_hull: number;
  roundness: number;
  center_of_mass_distance: number;
  center_of_mass_x: number;
  center_of_mass_y: number;
  hue: number;
  saturation: number;
  intensity: number;
  fluorescence: number;
  // [key: `h${number}`]: number;
  // [key: `s${number}`]: number;
  // [key: `v${number}`]: number;
  // [key: `f${number}`]: number;
}[];

export type IndoorProjectDataSpreadsheetSideAvg = {
  filename: string;
  images: string[];
  exp_id: number;
  pot_barcode: number;
  variety: string;
  treatment: string;
  scan_time: string;
  scan_date: string;
  dfp: number;
  view: string;
  width: number;
  height: number;
  surface: number;
  convex_hull: number;
  roundness: number;
  center_of_mass_distance: number;
  center_of_mass_x: number;
  center_of_mass_y: number;
  hue: number;
  saturation: number;
  intensity: number;
  fluorescence: number;
}[];

export type IndoorProjectDataPlantAPIResponse = {
  ppew: {
    exp_id: number;
    treatment: string;
    species_name: string;
    entry: string;
    pot_barcode: number;
    planting_date: Date;
    pottype: string;
    ct_configuration: string;
    variety: string;
    year: number;
    pi: string;
  };
  top: IndoorProjectDataSpreadsheetTop;
  // side_all: {
  //   filename: string;
  //   exp_id: number;
  //   pot_barcode: number;
  //   variety: string;
  //   treatment: string;
  //   scan_time: string;
  //   scan_date: string;
  //   dfp: number;
  //   view: string;
  //   frame_nr: number;
  //   width: number;
  //   height: number;
  //   surface: number;
  //   convex_hull: number;
  //   roundness: number;
  //   center_of_mass_distance: number;
  //   center_of_mass_x: number;
  //   center_of_mass_y: number;
  //   hue: number;
  //   saturation: number;
  //   intensity: number;
  //   fluorescence: number;
  // }[];
  side_avg: IndoorProjectDataSpreadsheetSideAvg;
};

export type IndoorProjectDataVizRecord = {
  hue: number | null;
  intensity: number | null;
  interval_days: number;
  saturation: number | null;
  group: string;
};

export type IndoorProjectDataVizAPIResponse = {
  results: IndoorProjectDataVizRecord[];
};

export type IndoorProjectDataViz2Record = {
  interval_days: number;
  group: string;
  [key: string]: number;
};

export type IndoorProjectDataViz2APIResponse = {
  results: IndoorProjectDataViz2Record[];
};

// Types for data visualization forms
export type CameraOrientation = 'top' | 'side';

export type CameraOrientationOptions = {
  label: string;
  value: CameraOrientation;
}[];

export type PlottedBy = 'groups' | 'pots';

export type PlottedByOptions = {
  label: string;
  value: PlottedBy;
}[];

export type AccordingTo =
  | 'treatment'
  | 'description'
  | 'treatment_description'
  | 'all'
  | string; // For individual pot IDs

export type AccordingToOptions = {
  label: string;
  value: AccordingTo;
}[];

// Generic type for form data
type FormData = {
  cameraOrientation: CameraOrientation;
  plottedBy: PlottedBy;
  accordingTo: AccordingTo;
};

interface FetchVisualizationParams {
  indoorProjectId: string;
  indoorProjectDataId: string;
  cameraOrientation: string;
  plottedBy: string;
  accordingTo: string;
  potBarcode?: number;
}

// Types for trait visualization form
export type TargetTrait = string;

export interface TraitModuleFormData extends FormData {
  targetTrait: TargetTrait;
}

export interface TraitModuleFormProps {
  indoorProjectId: string;
  indoorProjectDataId: string;
  numericColumns: NumericColumns;
  potBarcodes: number[];
  setVisualizationData: React.Dispatch<
    React.SetStateAction<IndoorProjectDataViz2APIResponse | null>
  >;
}

export interface FetchTraitModuleParams extends FetchVisualizationParams {
  targetTrait: string;
}

// Types for trait scatter plot visualization form
export interface TraitScatterModuleFormData extends FormData {
  targetTraitX: TargetTrait;
  targetTraitY: TargetTrait;
}

export interface TraitScatterModuleFormProps {
  indoorProjectId: string;
  indoorProjectDataId: string;
  numericColumns: NumericColumns;
  potBarcodes: number[];
  setVisualizationData: React.Dispatch<
    React.SetStateAction<IndoorProjectDataVizScatterAPIResponse | null>
  >;
}

export interface FetchTraitScatterModuleParams
  extends FetchVisualizationParams {
  targetTraitX: string;
  targetTraitY: string;
}

export type IndoorProjectDataVizScatterRecord = {
  interval_days: number;
  group: string;
  x: number;
  y: number;
  id: string;
};

export type IndoorProjectDataVizScatterAPIResponse = {
  results: IndoorProjectDataVizScatterRecord[];
  traits: {
    x: string;
    y: string;
  };
};

// Types for pot group visualization form
export type PotGroupModuleFormData = FormData;

export interface PotGroupModuleFormProps {
  indoorProjectId: string;
  indoorProjectDataId: string;
  potBarcodes: number[];
  setVisualizationData: React.Dispatch<
    React.SetStateAction<IndoorProjectDataVizAPIResponse | null>
  >;
}

export type FetchPotGroupModuleParams = FetchVisualizationParams;

// Types for pot visualization
export interface CircleItemProps {
  group: IndoorProjectDataVizRecord;
  treatment: string;
  hsvColor: {
    hue: number;
    saturation: number;
    intensity: number;
  };
  url: string;
}

export interface PotModuleDataVisualizationProps {
  data: IndoorProjectDataVizAPIResponse;
  indoorProjectDataSpreadsheet: IndoorProjectDataSpreadsheetAPIResponse;
  indoorProjectId: string;
}

export interface SliderMark {
  value: number;
  label: string;
}

export interface IndoorProjectUploadInputProps {
  indoorProjectId: string;
  activeTreatment?: string | null;
}
