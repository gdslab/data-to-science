import { Feature, FeatureCollection, Geometry, Point } from 'geojson';

import { FieldCampaignInitialValues } from './fieldCampaigns/FieldCampaign';
import {
  SingleBandSymbology,
  MultibandSymbology,
} from '../../maps/RasterSymbologyContext';
import { Team } from '../teams/Teams';

// raster band info from gdalinfo
export interface Band {
  data_type: string;
  nodata: string | null;
  stats: {
    maximum: number;
    mean: number;
    minimum: number;
    stddev: number;
  };
  unit: string;
}

// geojson object collected from leaflet
export type Coordinates = number[][];

// data product object returned from api
export interface DataProduct {
  id: string;
  bbox?: [number, number, number, number];
  crs?: {
    epsg: number;
    unit: string;
  };
  data_type: string;
  filepath: string;
  flight_id: string;
  original_filename: string;
  public: boolean;
  resolution?: {
    unit: string;
    x: number;
    y: number;
  };
  signature?: {
    expires: number;
    secure: string;
  };
  stac_properties: STACProperties;
  status: string;
  url: string;
  user_style: SingleBandSymbology | MultibandSymbology;
}

// earth observation info from gdalinfo
export interface EO {
  description: string;
  name: string;
}

export type FieldCampaign = {
  id: string;
  form_data: FieldCampaignInitialValues;
  lead_id: string;
  title: string;
};

// geojson object representing project field boundary
export type FieldGeoJSONFeature = Omit<Feature, 'properties'> & {
  properties: {
    [key: string]: string;
  };
};

// flight object returned from api
export interface Flight {
  id: string;
  acquisition_date: string;
  altitude: number;
  data_products: DataProduct[];
  forward_overlap: number;
  name: string | null;
  pilot_id: string;
  platform: string;
  project_id: string;
  sensor: string;
  side_overlap: number;
}

export interface GeoJSONFeature {
  geometry: {
    coordinates: Coordinates[] | Coordinates[][];
    type: string;
  };
  properties: {
    [key: string]: string;
  };
  type: string;
}

export type IForester = {
  id: string;
  dbh: number;
  depthFile: string;
  distance: number;
  imageFile: string;
  latitude: number;
  longitude: number;
  note: string;
  phoneDirection: number;
  phoneID: string;
  species: string;
  timeStamp: string;
  user: string;
};

export type Job = {
  id: string;
  data_product_id: string;
  end_time: string;
  extra: { [key: string]: unknown };
  name: string;
  raw_data_id: string;
  start_time: string;
  state: string;
  status: string;
};

export interface Location {
  center: {
    lat: number;
    lng: number;
  };
  geojson: GeoJSONFeature;
  type: string;
}

export type MapLayer = {
  fgb_url: string;
  geom_type: string;
  layer_id: string;
  layer_name: string;
  parquet_url: string;
  preview_url: string;
  signed_url: string;
};

type MapLayerProperties = {
  id: string;
  layer_id: string;
  layer_name: string;
  properties?: { [key: string]: unknown };
};

type MapLayerFeature<
  G extends Geometry | null = Geometry,
  P = MapLayerProperties
> = Feature<G, P>;

export interface MapLayerFeatureCollection<
  G extends Geometry | null = Geometry,
  P = MapLayerProperties
> extends FeatureCollection<G, P> {
  features: Array<MapLayerFeature<G, P>>;
  metadata: {
    preview_url: string;
  };
}

// pilot for flight
export interface Pilot {
  label: string;
  value: string;
}

// project object returned from api (detail view)
export interface ProjectDetail {
  id: string;
  created_at: string;
  created_by: {
    email: string;
    first_name: string;
    last_name: string;
  } | null;
  data_product_count: number;
  deactivated_at: string | null;
  description: string;
  field: GeoJSONFeature;
  flight_count: number;
  harvest_date: string;
  is_active: boolean;
  is_published: boolean;
  location_id: string;
  most_recent_flight: string | null;
  planting_date: string;
  role: string;
  team_id: string;
  title: string;
  updated_at: string;
}

// Feature collection of project point features with custom properties
export type ProjectFeatureCollection = FeatureCollection<
  Point,
  ProjectPointFeatureProperties
>;

// project object returned from api (list view)
export interface ProjectItem {
  id: string;
  centroid: {
    x: number;
    y: number;
  };
  data_product_count: number;
  description: string;
  field: FieldGeoJSONFeature;
  flight_count: number;
  liked: boolean;
  location_id: string;
  most_recent_flight: string;
  role: string;
  team: Team | null;
  team_id: string;
  title: string;
}

// project data initially loaded on project detail page
export interface ProjectLoaderData {
  fieldCampaigns: FieldCampaign[];
  flights: Flight[];
  pilots: Pilot[];
  project: ProjectDetail;
  project_modules: ProjectModule[];
  role: string;
  teams: Team[];
}

export interface ProjectModule {
  id: string;
  description?: string;
  enabled: boolean;
  label?: string;
  module_name: string;
  project_id: string;
  required?: boolean;
  sort_order?: number;
}

// Properties for a project point feature
export interface ProjectPointFeatureProperties {
  id: string;
  description: string;
  title: string;
}

// Project point feature with custom properties
export type ProjectPointFeature = Feature<Point, ProjectPointFeatureProperties>;

export type SetLocation = React.Dispatch<React.SetStateAction<Location | null>>;

export type STACProperties = {
  eo: EO[];
  raster: Band[];
};

type ZonalFeatureProperties = {
  id: string;
  count: number;
  max: number;
  mean: number;
  median: number;
  min: number;
  std: number;
  [key: string]: string | number;
};

export type ZonalFeature<
  G extends Geometry | null = Geometry,
  P = ZonalFeatureProperties
> = Feature<G, P>;

export interface ZonalFeatureCollection<
  G extends Geometry | null = Geometry,
  P = ZonalFeatureProperties
> extends FeatureCollection<G, P> {
  features: Array<ZonalFeature<G, P>>;
}
