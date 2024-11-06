export type StorageAvailability = {
  used: number;
  total: number;
  free: number;
};

type DTypeCount = {
  name: string;
  count: number;
};

export type SiteStatistics = {
  data_product_count: number;
  data_product_dtype_count: {
    first: DTypeCount | null;
    second: DTypeCount | null;
    third: DTypeCount | null;
    other: DTypeCount | null;
  };
  flight_count: number;
  project_count: number;
  storage_availability: StorageAvailability;
  user_count: number;
};

export type ProjectStatistics = {
  id: string;
  user: string;
  total_projects: number;
  total_active_projects: number;
  total_storage: number;
  total_active_storage: number;
};
