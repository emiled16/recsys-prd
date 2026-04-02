# Online Feature Requirements

## Purpose
This document defines which features must be available during online inference, how fresh they must be, and which streaming inputs are responsible for keeping them current.

The goal is to separate genuinely latency-sensitive features from features that can remain offline-only or batch-refreshed.

## Online Entities

### `customer_session`
- Join keys:
  - `customer_id`
  - `session_id`
- Purpose:
  - capture short-horizon user intent and recent engagement
- Updated by:
  - `product_view`
  - `product_click`
  - `add_to_cart`
  - `wishlist_add`
  - `search_query`

### `customer`
- Join key:
  - `customer_id`
- Purpose:
  - expose near-real-time customer aggregates that affect ranking
- Updated by:
  - `purchase`
  - `add_to_cart`
  - `wishlist_add`

### `article`
- Join key:
  - `article_id`
- Purpose:
  - expose popularity, price, and inventory-sensitive article state
- Updated by:
  - `purchase`
  - `inventory_update`
  - `price_change`
  - `product_metadata_update`

## Required Online Feature Sets

### `session_intent_features`
- Entity: `customer_session`
- Freshness target: under 60 seconds
- Serving need:
  - required for ranking and request-context-aware retrieval
- Streaming inputs:
  - `product_view`
  - `product_click`
  - `add_to_cart`
  - `wishlist_add`
  - `search_query`
- Fields:
  - `recent_viewed_article_ids`
  - `recent_clicked_article_ids`
  - `recent_search_terms`
  - `cart_add_count_30m`
  - `wishlist_add_count_7d`
  - `last_event_time`

### `customer_realtime_features`
- Entity: `customer`
- Freshness target: under 5 minutes
- Serving need:
  - ranking features for intent, value, and purchase propensity
- Streaming inputs:
  - `purchase`
  - `add_to_cart`
  - `wishlist_add`
- Fields:
  - `purchase_count_30d_rt`
  - `purchase_count_7d_rt`
  - `days_since_last_purchase_rt`
  - `cart_add_count_7d_rt`
  - `wishlist_add_count_30d_rt`

### `article_realtime_features`
- Entity: `article`
- Freshness target: under 2 minutes
- Serving need:
  - retrieval priors, inventory-aware ranking, and current price signals
- Streaming inputs:
  - `purchase`
  - `inventory_update`
  - `price_change`
  - `product_metadata_update`
- Fields:
  - `purchase_count_1d_rt`
  - `purchase_count_7d_rt`
  - `inventory_level_rt`
  - `is_in_stock_rt`
  - `current_price_rt`
  - `minutes_since_last_catalog_update`

## Offline-Only Feature Sets
- static profile features such as age or membership status
- static catalog attributes such as department or product group
- heavy historical aggregates that do not require sub-hour freshness

These remain batch or snapshot inputs and can be joined at inference from cached offline-derived stores if needed.

## Consistency Requirements
- Online feature names should map cleanly to the offline logical equivalents where the semantics overlap.
- When freshness-driven deviations exist, the naming should make the realtime scope explicit, for example `_rt`.
- Missing online features must have deterministic fallback behavior at inference time.

## Acceptance Criteria
- The required online feature sets, freshness targets, and streaming inputs are explicit.
- The contract is specific enough to guide streaming computation in `T20` and serving in `T21`.
