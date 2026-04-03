export type RecommendationRequest = {
  customer_id?: string;
  session_id?: string;
  query_text?: string;
  seed_article_ids?: string[];
  limit?: number;
  timeout_ms?: number;
};

export type RecommendationItem = {
  article_id: string;
  score: number;
  source: string;
  rank: number;
  metadata: Record<string, string>;
};

export type RecommendationResponse = {
  response_id: string;
  experiment: string;
  variant: string;
  fallback_used: boolean;
  recommendations: RecommendationItem[];
  warnings: string[];
};

export type TrackingEvent = {
  event_type:
    | "product_view"
    | "product_click"
    | "add_to_cart"
    | "wishlist_add"
    | "purchase"
    | "search_query";
  customer_id: string;
  session_id: string;
  article_id?: string;
  query_text?: string;
  price?: number;
  source?: string;
  event_time?: string;
};

export type ReadinessResponse = {
  ready: boolean;
  checked_at_utc: string;
  components: Record<string, boolean>;
};

export type DiagnosticResponse = {
  service_name: string;
  version: string;
  environment: string;
  ready: boolean;
  supported_endpoints: string[];
  supported_event_types: string[];
  capability_flags: Record<string, boolean>;
  contract_notes: string[];
  safe_state: Record<string, unknown>;
};
