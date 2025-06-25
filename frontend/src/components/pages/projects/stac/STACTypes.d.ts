export interface STACItem {
  id: string;
  type: string;
  properties: {
    title?: string;
    datetime: string;
    data_product_details: {
      data_type: string;
    };
    flight_details: {
      acquisition_date: string;
      platform: string;
      sensor: string;
    };
  };
  browser_url?: string;
}

export interface STACError {
  code: string;
  message: string;
  timestamp: string;
  details?: {
    data_product_id: string;
    data_type: string;
    filepath: string;
    flight_id: string;
    title?: string;
    acquisition_date?: string;
    platform?: string;
    sensor?: string;
  };
}

export interface ItemStatus {
  item_id: string;
  is_published: boolean;
  item_url?: string;
  error?: STACError;
}

export interface STACMetadata {
  collection_id: string;
  collection: {
    id: string;
    title: string;
    description: string;
    extent: {
      spatial: {
        bbox: number[][];
      };
      temporal: {
        interval: string[][];
      };
    };
    'sci:doi'?: string;
    'sci:citation'?: string;
  };
  items: Array<STACItem | ItemStatus>;
  is_published: boolean;
  collection_url?: string;
  failed_items?: Array<ItemStatus>;
}

export interface CombinedSTACItem {
  id: string;
  isSuccessful: boolean;
  title?: string;
  dataType?: string;
  acquisitionDate?: string;
  platform?: string;
  sensor?: string;
  browserUrl?: string;
  error?: STACError;
}
