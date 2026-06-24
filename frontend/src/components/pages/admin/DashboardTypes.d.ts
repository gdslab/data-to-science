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
  public_data_product_count: number;
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

export type ActivationFunnel = {
  signed_up: number;
  email_confirmed: number;
  approved: number;
  created_project: number;
};

export type ActivitySummary = {
  active_24h: number;
  active_7d: number;
  active_30d: number;
  total_users: number;
  funnel: ActivationFunnel;
};

export type ActivityTrendPoint = {
  snapshot_date: string;
  active_24h: number;
  active_7d: number;
  active_30d: number;
  new_users: number;
  stickiness: number;
};

export type LeaderboardMetric =
  | 'projects'
  | 'flights'
  | 'data_products'
  | 'views'
  | 'likes'
  | 'storage';

export type EngagementLeaderRow = {
  user_id: string;
  name: string;
  email: string;
  project_count: number;
  flight_count: number;
  data_product_count: number;
  total_views: number;
  total_likes: number;
  total_storage: number;
};
