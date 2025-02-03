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

export type IndoorProjectDataAPIResponse = {
  id: string;
  original_filename: string;
  stored_filename: string;
  file_path: string;
  file_size: number;
  file_type: string;
  directory_structure?: {
    name: string;
    type: string;
    children: {
      name: string;
      type: string;
      size?: number;
    }[];
  };
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
    planting_date: Date[];
    pottype: string[];
    ct_configuration: string[];
    variety: string[];
    year: number[];
    pi: string[];
  };
  numeric_columns: NumericColumns;
};

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
  top: {
    filename: string;
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
    [key: `h${number}`]: number;
    [key: `s${number}`]: number;
    [key: `v${number}`]: number;
    [key: `f${number}`]: number;
  }[];
  side_all: {
    filename: string;
    exp_id: number;
    pot_barcode: number;
    variety: string;
    treatment: string;
    scan_time: string;
    scan_date: string;
    dfp: number;
    view: string;
    frame_nr: number;
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
  side_avg: {
    filename: string;
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
};

export type IndoorProjectDataVizRecord = {
  hue: number | null;
  intensity: number | null;
  interval_days: number;
  saturation: number | null;
  treatment: string;
};

export type IndoorProjectDataVizAPIResponse = {
  results: IndoorProjectDataVizRecord[];
};

export type IndoorProjectDataViz2Record = {
  interval_days: number;
  treatment: string;
  [key: string]: number;
};

export type IndoorProjectDataViz2APIResponse = {
  results: IndoorProjectDataViz2Record[];
};
