# Offline Feature Entities and Views

## Purpose
This document defines the first offline feature-platform contract for training and batch scoring. It identifies the entities, offline feature views, source datasets, join keys, and timestamps that later point-in-time retrieval must honor.

## Entity Definitions

### `customer`
- Join key: `customer_id`
- Source of truth: `data/normalized/customers/customers_normalized.csv`
- Cardinality: one row per customer
- Used by:
  - customer profile features
  - customer historical activity aggregates
  - ranking and retrieval user-context features

### `article`
- Join key: `article_id`
- Source of truth: `data/normalized/products/products_normalized.csv`
- Cardinality: one row per article
- Used by:
  - product catalog features
  - multimodal product descriptors
  - inventory- and popularity-aware ranking features

### `customer_article`
- Composite join key: `customer_id`, `article_id`
- Source of truth: derived from `transactions_normalized`
- Cardinality: zero or more rows per customer-article pair over time
- Used by:
  - affinity and recency features
  - repeat purchase indicators
  - interaction-history joins for ranking

## Offline Feature Views

### `customer_profile_features`
- Entity: `customer`
- Source mapping:
  - base source: `customers_normalized`
- Timestamp column: none for the static baseline slice; snapshot timestamp added at materialization time
- Feature fields:
  - `age`
  - `club_member_status`
  - `fashion_news_frequency`
  - `has_fn_flag`
  - `has_active_flag`
- Notes:
  - This is a slowly changing profile-style view.
  - It is expected to be snapshotted when exported for training.

### `article_catalog_features`
- Entity: `article`
- Source mapping:
  - base source: `products_normalized`
  - auxiliary source: `product_images_manifest`
- Timestamp column: none for the static baseline slice; snapshot timestamp added at materialization time
- Feature fields:
  - `product_type_name`
  - `product_group_name`
  - `colour_group_name`
  - `department_name`
  - `index_group_name`
  - `has_detail_desc`
  - `has_image`
- Notes:
  - This view is the structured catalog baseline for retrieval and ranking.
  - Later embedding metadata can be attached without changing the entity boundary.

### `customer_activity_features`
- Entity: `customer`
- Source mapping:
  - base source: `transactions_normalized`
- Timestamp column: `event_time`
- Window semantics:
  - all-time up to event time
  - trailing 30-day window
- Feature fields:
  - `purchase_count_30d`
  - `purchase_count_all_time`
  - `days_since_last_purchase`
  - `distinct_articles_purchased_30d`
  - `avg_purchase_price_30d`
- Notes:
  - This view must be materialized point-in-time correctly.
  - Leakage prevention depends on filtering strictly to events before the label timestamp.

### `article_demand_features`
- Entity: `article`
- Source mapping:
  - base source: `transactions_normalized`
- Timestamp column: `event_time`
- Window semantics:
  - trailing 7-day window
  - trailing 30-day window
- Feature fields:
  - `purchase_count_7d`
  - `purchase_count_30d`
  - `unique_customers_30d`
  - `avg_article_price_30d`
  - `days_since_last_article_purchase`
- Notes:
  - This view is used for popularity-sensitive ranking and retrieval priors.

### `customer_article_affinity_features`
- Entity: `customer_article`
- Source mapping:
  - base source: `transactions_normalized`
- Timestamp column: `event_time`
- Window semantics:
  - all-time up to event time
- Feature fields:
  - `historical_purchase_count`
  - `days_since_last_purchase`
  - `has_purchased_before`
  - `last_purchase_price`
- Notes:
  - This view captures direct affinity between a customer and candidate article.
  - It is only available when the customer-article pair exists historically.

## Training Join Guidance
- Labels come from `transactions_normalized`.
- Entity rows are built around a label timestamp and candidate `article_id`.
- Static views are snapped as of the training run snapshot date.
- Event-time views must be filtered strictly to records earlier than the label timestamp.

## Batch Scoring Guidance
- Customer and article static views can be materialized daily.
- Activity and demand aggregates can be recomputed on a daily batch schedule for offline scoring.
- The same logical feature names should later map to online equivalents where freshness requirements justify them.

## Acceptance Criteria
- Feature entities and view boundaries are explicit.
- Source mappings and timestamps are documented for each view.
- The spec is concrete enough to drive point-in-time training joins in `T18`.
