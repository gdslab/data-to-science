import { FieldCampaignInitialValues } from './fieldCampaigns/FieldCampaign';

// geojson object representing project field boundary
export type FieldGeoJSONFeature = Omit<GeoJSON.Feature, 'properties'> & {
  properties: {
    [key: string]: string;
  };
};

// geojson object collected from leaflet
export type Coordinates = number[][];
export interface GeoJSONFeature {
  type: string;
  geometry: {
    type: string;
    coordinates: Coordinates[] | Coordinates[][];
  };
  properties: {
    [key: string]: string;
  };
}

type FieldGeoJSONFeature = Omit<GeoJSON.Feature, 'properties'> & {
  properties: FieldProperties;
};

type MapLayerFeature = Omit<GeoJSON.Feature, 'properties'> & {
  properties: {
    id: string;
    layer_id: string;
    layer_name: string;
    properties?: { [key: string]: any };
  };
};

export type MapLayerFeatureCollection = GeoJSON.FeatureCollection<MapLayerFeature>;

export interface FeatureCollection {
  type: 'FeatureCollection';
  features: GeoJSON.Feature[];
}

export interface Location {
  geojson: GeoJSONFeature;
  center: {
    lat: number;
    lng: number;
  };
  type: string;
}

export type SetLocation = React.Dispatch<React.SetStateAction<Location | null>>;

// project object returned from api
export interface Project {
  id: string;
  title: string;
  description: string;
  planting_date: string;
  harvest_date: string;
  location_id: string;
  team_id: string;
  flight_count: number;
  owner_id: string;
  is_owner: boolean;
  field: GeoJSONFeature;
}

// raster band info from gdalinfo
export interface Band {
  data_type: string;
  nodata: string | null;
  stats: {
    mean: number;
    stddev: number;
    maximum: number;
    minimum: number;
  };
  unit: string;
}

// earth observation info from gdalinfo
export interface EO {
  name: string;
  description: string;
}

// data product object returned from api
export interface DataProduct {
  id: string;
  data_type: string;
  original_filename: string;
  filepath: string;
  url: string;
  flight_id: string;
  public: boolean;
  stac_properties: {
    raster: Band[];
    eo: EO[];
  };
  user_style: SymbologySettings;
}

// flight object returned from api
export interface Flight {
  id: string;
  acquisition_date: string;
  altitude: number;
  side_overlap: number;
  forward_overlap: number;
  sensor: string;
  platform: string;
  project_id: string;
  pilot_id: string;
  data_products: DataProduct[];
}

// pilot for flight
export interface Pilot {
  label: string;
  value: string;
}

// project data initially loaded on project detail page
export interface ProjectLoaderData {
  pilots: Pilot[];
  project: Project;
  role: string;
  fieldCampaigns: FieldCampaign[];
  flights: Flight[];
  teams: Team[];
}

export type FieldCampaign = {
  id: string;
  title: string;
  lead_id: string;
  form_data: FieldCampaignInitialValues;
};
