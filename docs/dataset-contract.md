# Source Dataset Contract

## Purpose
This document defines the source-of-truth contract for the historical H&M dataset that feeds ingestion, normalization, feature generation, and evaluation workflows.

The contract is intentionally strict about identifiers, timestamps, and required fields because downstream recommendation components depend on stable joins and point-in-time correctness.

## Source Tables

### `customers`
Primary key: `customer_id`

Required fields:
- `customer_id`: Stable customer identifier from the source dataset.
- `FN`: Nullable flag carried through as a raw attribute.
- `Active`: Nullable activity flag carried through as a raw attribute.
- `club_member_status`: Membership status string.
- `fashion_news_frequency`: Marketing/news preference string.
- `age`: Customer age in years when available.
- `postal_code`: Raw postal code string.

Quality rules:
- `customer_id` must be unique and non-null.
- `age` may be null, but if present it must be numeric and non-negative.
- Categorical strings should be trimmed and normalized for casing during normalization.
- Raw nulls or sentinel values such as `NONE` must be preserved in the raw layer and standardized only in normalized outputs.

Downstream expectations:
- `customer_id` remains the canonical join key across transactions, features, and recommendation logs.
- PII is limited to coarse demographic fields already present in the dataset; no additional personal data should be introduced locally.

### `articles`
Primary key: `article_id`

Required fields:
- `article_id`: Stable product identifier from the source dataset.
- `product_code`
- `prod_name`
- `product_type_name`
- `product_group_name`
- `graphical_appearance_name`
- `colour_group_name`
- `perceived_colour_value_name`
- `perceived_colour_master_name`
- `department_name`
- `index_name`
- `index_group_name`
- `section_name`
- `garment_group_name`
- `detail_desc`: Nullable free-text product description.

Quality rules:
- `article_id` must be unique and non-null.
- Text columns may be null only where the source dataset permits it, with `detail_desc` expected to have the highest null rate.
- Product taxonomy fields should remain internally consistent after normalization; for example, a row cannot lose `product_group_name` while retaining lower-level category fields.
- Duplicate `article_id` rows are not allowed in normalized outputs.

Downstream expectations:
- `article_id` is the canonical product key across catalog, image assets, embeddings, vector indexing, and serving.
- Text and structured attributes must remain available for multimodal embedding generation.

### `transactions_train`
Logical primary key: no single-column key in source; normalized event key will be derived.

Required fields:
- `t_dat`: Transaction date.
- `customer_id`
- `article_id`
- `price`
- `sales_channel_id`

Quality rules:
- `customer_id` and `article_id` must be non-null.
- `t_dat` must parse into a valid event timestamp.
- `price` must be numeric and non-negative.
- `sales_channel_id` must map to a constrained local enum or documented integer set during normalization.
- Exact duplicate rows in the raw layer may be retained for auditability, but normalized transaction events must expose a deterministic event identifier.

Downstream expectations:
- Transactions are the historical supervision backbone for training, evaluation, and synthetic replay.
- Normalized outputs must support point-in-time joins keyed by event timestamp.

### `images`
Logical primary key: one or more image assets per `article_id`

Required fields:
- `article_id`: Parsed from the file naming convention or image manifest.
- `image_path`: Relative or absolute path to the local image asset.
- `image_kind`: Default `product` unless additional image classes are introduced later.

Quality rules:
- Every image row must resolve to a valid `article_id`.
- `image_path` must exist on disk in the raw asset layer when ingestion completes.
- Multiple images per article are allowed, but each `(article_id, image_path)` pair must be unique.
- Missing images are allowed for a subset of catalog rows, but coverage must be measurable and reported.

Downstream expectations:
- Image assets must be discoverable without scanning arbitrary directories.
- Image records must preserve enough provenance to regenerate embeddings deterministically.

## Canonical Identifier Rules
- `customer_id` and `article_id` are stored as strings end to end, even if they look numeric, to avoid formatting drift.
- Raw source identifiers are never re-assigned.
- Derived normalized event identifiers must be deterministic and reproducible from source columns.

## Timestamp Rules
- Raw transaction dates must be normalized into timezone-aware timestamps during downstream processing.
- Historical training data should treat transaction time as the event time of record.
- Synthetic streaming events must preserve an explicit `event_time` that can be traced back to the source transaction or replay seed.

## Null and Missing Data Rules
- The raw layer preserves source nulls exactly.
- The normalized layer may replace sentinel values, trim whitespace, and standardize categories, but it must not silently invent business semantics.
- Imputation for modeling belongs in feature pipelines, not in the raw contract.

## Expected Normalized Outputs
The first normalization pass must produce these stable entities:
- `products_normalized`
- `customers_normalized`
- `transactions_normalized`
- `product_images_manifest`

Each output must publish:
- schema definition,
- row-count snapshot,
- uniqueness guarantees for its primary key,
- null-rate summary for important fields.

## Surface Ownership
- `pipelines/` owns normalization and publication of the normalized entities above.
- `simulator/` may read normalized outputs to derive replay batches but must not mutate them.
- `backend/` may read normalized outputs only through documented file paths and schemas; it must not rely on pipelines-private helper functions as the contract.

## Backend-Visible Pipeline Outputs
The backend may consume these pipeline-published artifacts:
- normalized entity datasets under `data/normalized/`
- point-in-time training datasets under `data/features/offline/training_dataset/`
- ranking datasets under `data/models/training_sets/ranking_dataset/`
- promoted model registry artifacts under `data/models/registry/`

The backend must treat file paths, field names, and documented manifests as the stable handoff.

## Acceptance Criteria
- All required source tables and image assets are mapped into documented contracts.
- Primary keys, required fields, and quality assumptions are explicit.
- The contract is specific enough to drive ingestion and validation tasks `T7` through `T11`.
