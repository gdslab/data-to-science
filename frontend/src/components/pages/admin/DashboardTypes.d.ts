export type StorageAvailability = {
  used: number;
  total: number;
  free: number;
};

export type SiteStatistics = {
  data_product_count: number;
  data_product_dtype_count: {
    dsm_count: number;
    ortho_count: number;
    point_cloud_count: number;
    other_count: number;
  };
  flight_count: number;
  project_count: number;
  storage_availability: StorageAvailability;
  user_count: number;
};
