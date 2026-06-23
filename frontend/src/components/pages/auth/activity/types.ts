export interface ViewsTrendPoint {
  week_start: string;
  views: number;
}

export interface DataProductStatRow {
  id: string;
  data_type: string;
  project_id: string;
  project_name: string;
  flight_id: string;
  flight_date: string;
  views: number;
  likes: number;
}

export interface RecentActivityRow {
  id: string;
  data_type: string;
  project_id: string;
  project_name: string;
  owner_name: string;
  flight_id: string;
  flight_date: string;
  last_action_at: string;
}

export interface OwnerStats {
  total_views: number;
  total_likes: number;
  data_product_count: number;
  public_count: number;
  project_count: number;
  views_trend: ViewsTrendPoint[];
  top_viewed: DataProductStatRow[];
  top_liked: DataProductStatRow[];
}

export interface ActivityCounts {
  viewed_count: number;
  liked_count: number;
  recently_viewed: RecentActivityRow[];
  recently_liked: RecentActivityRow[];
}

export interface ProfileStats {
  received: OwnerStats;
  activity: ActivityCounts;
}
