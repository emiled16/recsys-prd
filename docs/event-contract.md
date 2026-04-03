# Simulated Event Contract

## Purpose
This document defines the local event schemas used to simulate online behavior from normalized H&M datasets. These schemas are the simulator-owned contract for synthetic generation, replay, validation, and future Kafka topic integration.

## Topic Boundaries

### `interaction_events`
Carries user-facing behavioral signals.

Supported event types:
- `product_view`
- `product_click`
- `add_to_cart`
- `wishlist_add`
- `purchase`
- `search_query`

Required fields:
- `event_id`
- `event_type`
- `event_time`
- `customer_id`
- `session_id`
- `source`

Conditional fields:
- `article_id`: Required for product interaction events.
- `price`: Required for `purchase`.
- `query_text`: Required for `search_query`.

Ordering rules:
- Events are ordered by `event_time`.
- For the same customer and session, `product_view` must precede `product_click`, which must precede `add_to_cart` or `wishlist_add`, which must precede `purchase` when those events coexist.

### `catalog_events`
Carries catalog or availability changes that affect online serving and freshness-sensitive features.

Supported event types:
- `inventory_update`
- `price_change`
- `product_metadata_update`

Required fields:
- `event_id`
- `event_type`
- `event_time`
- `article_id`
- `source`

Conditional fields:
- `inventory_delta` and `inventory_level`: Present for `inventory_update`.
- `old_price` and `new_price`: Present for `price_change`.
- `changed_fields`: Present for `product_metadata_update`.

Ordering rules:
- Events are ordered by `event_time`.
- For the same `article_id`, price or metadata updates must not move backward in time within a replay batch.

### `recommendation_tracking_events`
Carries frontend-to-backend telemetry for recommendation exposures, clicks, and explicit feedback.

Supported event types:
- `recommendation_exposure`
- `recommendation_click`
- `recommendation_feedback`

Required fields:
- `event_type`
- `event_time`
- `customer_id`
- `session_id`
- `response_id`

Conditional fields:
- `article_id`: Required for `recommendation_click` and optional for `recommendation_feedback`.
- `query_text`: Optional for exposure and click events, but valid as feedback context when an
  article is not present.
- `metadata`: Optional key-value bag for UI surface, placement, or request-context diagnostics.

Ordering rules:
- Exposure should be emitted before click or feedback for the same `response_id`.
- Multiple UI actions for the same `response_id` must not move backward in time.

## Common Envelope Rules
- `event_id` must be deterministic from the source row and replay step.
- `event_time` must be an ISO 8601 UTC timestamp.
- `source` identifies whether the event was derived from historical transactions or catalog synthesis.
- Payloads must be JSON-serializable and line-delimited for replay.

## Local Replay Conventions
- Replay batches are written under `data/events/replay_batches/`.
- Each topic has its own JSON Lines file.
- A replay manifest records source inputs, row counts, and the generation timestamp.
- `simulator/` owns replay-batch generation and manifest writing.
- Replay generation, replay validation, and fake traffic helpers belong to `simulator/` rather than
  `backend/recsys_prd/events`.
- Shared JSONL helpers and event ID builders live under `recsys_prd.io.*` because they are
  cross-runtime utilities rather than simulator runtime entrypoints.
- `backend/` consumes replay batches through these topic files or equivalent broker topics without importing simulator implementation details.
- Public recommendation tracking events are accepted through `POST /events` and written as
  append-only JSONL audit records under `data/reports/experiments/` in local development.

## Replay Manifest Contract
- `manifest.json` is written beside the replay topic files.
- The manifest must include `generated_at_utc`.
- The manifest must include one entry per topic with:
  - `path`
  - `row_count`
- Topic file rows must remain sorted by `(event_time, event_id)` so backend consumers and validators can replay deterministically.

## Boundary Rules
- The simulator may read normalized datasets to derive synthetic traffic.
- The simulator owns:
  - deterministic replay-batch generation
  - replay manifest writing
  - replay validation
  - fake traffic producers that emit the same topic contracts
- The backend may consume `interaction_events` and `catalog_events` payloads, but it must treat the payload schema and manifest as the public handoff.
- The backend must not reach into simulator implementation modules when reading replay artifacts;
  it should consume `simulator.*` entrypoints or shared artifact IO helpers only.
- The frontend may emit recommendation tracking events only through the public `POST /events`
  contract and should not publish directly to broker topics or write local files.
- Future non-simulator producers must emit the same topic contract if they are intended to replace local fake traffic.

## Acceptance Criteria
- Interaction and catalog schemas are explicit enough to drive tasks `T13` through `T16`.
- Topic boundaries, required fields, and ordering expectations are documented.
