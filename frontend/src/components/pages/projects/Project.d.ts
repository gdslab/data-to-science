import { Feature, FeatureCollection, Geometry } from 'geojson';

import { FieldCampaignInitialValues } from './fieldCampaigns/FieldCampaign';

// geojson object representing project field boundary
export type FieldGeoJSONFeature = Omit<Feature, 'properties'> & {
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

type FieldGeoJSONFeature = Omit<Feature, 'properties'> & {
  properties: FieldProperties;
};

type MapLayerProperties = {
  id: string;
  layer_id: string;
  layer_name: string;
  properties?: { [key: string]: any };
};

interface MapLayerFeature<G extends Geometry | null = Geometry, P = MapLayerProperties>
  extends Feature<G, P> {}

// export interface MapLayerFeatureCollection
//   extends FeatureCollection<MapLayerFeature> {
//   metadata: {
//     preview_url: string;
//   };
// }

export interface MapLayerFeatureCollection<
  G extends Geometry | null = Geometry,
  P = MapLayerProperties
> extends FeatureCollection<G, P> {
  features: Array<MapLayerFeature<G, P>>;
  metadata: {
    preview_url: string;
  };
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
  description: string;
  field: GeoJSONFeature;
  flight_count: number;
  harvest_date: string;
  location_id: string;
  planting_date: string;
  team_id: string;
  title: string;
  role: string;
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
  status: string;
  user_style: SymbologySettings;
}

// flight object returned from api
export interface Flight {
  id: string;
  name: string | null;
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

export type Job = {
  id: string;
  name: string;
  extra: { [key: string]: any };
  state: string;
  status: string;
  start_time: string;
  end_time: string;
  data_product_id: string;
  raw_data_id: string;
};

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
  user: string;
  timeStamp: Date;
};
