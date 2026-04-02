# Simulated Event Contract

## Purpose
This document defines the local event schemas used to simulate online behavior from normalized H&M datasets. These schemas are the contract for synthetic generation, replay, validation, and future Kafka topic integration.

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

## Common Envelope Rules
- `event_id` must be deterministic from the source row and replay step.
- `event_time` must be an ISO 8601 UTC timestamp.
- `source` identifies whether the event was derived from historical transactions or catalog synthesis.
- Payloads must be JSON-serializable and line-delimited for replay.

## Local Replay Conventions
- Replay batches are written under `data/events/replay_batches/`.
- Each topic has its own JSON Lines file.
- A replay manifest records source inputs, row counts, and the generation timestamp.

## Acceptance Criteria
- Interaction and catalog schemas are explicit enough to drive tasks `T13` through `T16`.
- Topic boundaries, required fields, and ordering expectations are documented.
