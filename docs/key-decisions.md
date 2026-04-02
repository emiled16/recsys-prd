# Key Decisions

## [2026-04-01] D-001: Treat H&M source identifiers as canonical strings
- Plan: v1.1
- Context: Downstream ingestion, normalization, and point-in-time joins need stable identifiers across raw files, feature generation, and serving.
- Options considered:
  - Preserve source identifiers as strings end to end.
  - Cast numeric-looking identifiers into integers during normalization.
- Decision: Preserve `customer_id` and `article_id` as canonical string identifiers throughout the platform.
- Rationale: String handling avoids formatting drift, leading-zero issues, and inconsistent joins across CSV, Parquet, features, and serving paths.
- Consequences: Validation and normalization code must enforce type consistency early, and downstream schemas should not assume numeric IDs.

## [2026-04-01] D-002: Use a layered `data/` directory as the local storage contract
- Plan: v1.1
- Context: The plan requires raw ingestion, normalization, features, replay, embeddings, indexes, and reports to coexist locally without ad hoc file placement.
- Options considered:
  - Store each subsystem's outputs beside its code.
  - Centralize data artifacts under a single layered `data/` root.
- Decision: Standardize all local project-managed datasets and derived artifacts under a top-level `data/` directory with explicit sublayers.
- Rationale: A layered storage contract makes pipeline ownership clearer, reduces path sprawl, and maps cleanly to later object-storage prefixes in production.
- Consequences: Future implementation tasks must read and write through configuration rooted at `data/`, and Git ignore rules will need to account for generated artifacts.

## [2026-04-01] D-003: Make raw ingestion work from either a zip archive or unpacked directory
- Plan: v1.1
- Context: The H&M dataset may arrive either as a downloaded archive or as an already unpacked directory depending on the local setup.
- Options considered:
  - Support only one input format and require manual preprocessing.
  - Accept both zip archives and directories in the ingestion command.
- Decision: The first ingestion command accepts either an unpacked dataset directory or a zip archive.
- Rationale: This keeps local onboarding simpler and makes the ingestion step reproducible regardless of how the dataset was obtained.
- Consequences: The ingestion module needs source discovery logic and tests for both paths, but users avoid manual extraction as a prerequisite.

## [2026-04-01] D-004: Reserve a top-level backend boundary for Python application code
- Plan: v1.1
- Context: The project is expected to grow into separate backend, frontend, and infrastructure areas rather than staying as a single-language repository.
- Options considered:
  - Keep Python code at the repository root.
  - Group Python application code, scripts, and tests under `backend/`.
- Decision: Move the Python package, backend scripts, and backend tests under `backend/`.
- Rationale: This keeps the monorepo layout compatible with future frontend and infra work and avoids mixing application boundaries too early.
- Consequences: Python commands should now run from or reference the `backend/` subtree, and future backend dependencies should be isolated there.

## [2026-04-01] D-005: Keep the first normalization slice dependency-light and CSV-based
- Plan: v1.1
- Context: The project needed working normalization and validation before a broader backend dependency stack had been introduced.
- Options considered:
  - Add dataframe or parquet dependencies immediately.
  - Use the Python standard library for the first normalization slice and emit CSV plus JSON metadata.
- Decision: Implement the initial normalization and validation pipeline with standard-library CSV and JSON outputs.
- Rationale: This keeps the early slice easy to run, easy to test, and aligned with the current lightweight backend setup.
- Consequences: Later feature and training work may migrate normalized outputs to Parquet once the backend data stack is introduced.

## [2026-04-01] D-006: Use artifact-based local replay before wiring a real message broker
- Plan: v1.1
- Context: The plan requires simulated online behavior now, but Kafka and broader local infrastructure are scheduled later in the roadmap.
- Options considered:
  - Introduce broker-specific publishing immediately.
  - Generate topic-scoped JSONL replay batches first and validate them as the stable local contract.
- Decision: Implement local replay as deterministic JSONL topic batches plus manifests before broker integration.
- Rationale: This keeps event generation and validation testable now while preserving a clean handoff to Kafka later.
- Consequences: Future streaming integration should treat these replay files as broker-ready payload sources rather than inventing a second event shape.

## [2026-04-01] D-007: Separate static and event-time offline feature views
- Plan: v1.1
- Context: The offline feature layer needs to support both stable profile/catalog attributes and leakage-sensitive historical aggregates.
- Options considered:
  - Treat all offline features as one undifferentiated set.
  - Split the registry into static snapshot views and event-time views with explicit timestamp semantics.
- Decision: Define offline feature views with explicit timestamp fields so static views are clearly separated from point-in-time aggregate views.
- Rationale: This keeps T18 simpler because the join logic only needs point-in-time filtering for the views that declare event-time semantics.
- Consequences: Future feature materialization code should preserve these semantics and avoid backfilling event-time features as if they were static snapshots.

## [2026-04-01] D-008: Build point-in-time joins with ordered historical replay before adopting a feature-store engine
- Plan: v1.1
- Context: The project needs leakage-safe training rows now, while Feast-style declarative retrieval and larger data tooling are still ahead in the plan.
- Options considered:
  - Delay training joins until a full feature-store stack is present.
  - Implement an ordered historical replay that computes each label row from prior events only.
- Decision: Build the first point-in-time training dataset by replaying normalized transactions in time order and deriving feature values from prior events only.
- Rationale: This makes the leakage boundary explicit, testable, and reproducible without blocking on future infrastructure choices.
- Consequences: Later feature-store integration should preserve the same join semantics even if the execution engine changes.

## [2026-04-01] D-009: Restrict online features to freshness-sensitive signals
- Plan: v1.1
- Context: Not every offline feature belongs in the online serving path, and pushing everything online would make T20 and T21 noisier than necessary.
- Options considered:
  - Mirror all offline features online.
  - Limit the online contract to session, customer-behavior, and article-state signals that need sub-hour freshness.
- Decision: Keep online feature requirements focused on session intent, realtime customer behavior, and realtime article state.
- Rationale: This keeps the serving path lean and reserves static profile or catalog attributes for batch/snapshot usage unless a clear latency need appears later.
- Consequences: T20 should prioritize a small number of high-value streaming aggregates instead of building a general-purpose online mirror of the offline feature set.

## [2026-04-01] D-010: Materialize online features into a file-backed local store before introducing Redis
- Plan: v1.1
- Context: The plan eventually calls for an online feature store, but the project still needs a concrete local serving artifact before infrastructure-heavy work lands.
- Options considered:
  - Block online feature work on Redis integration.
  - Compute the feature snapshots now and store them in a simple file-backed local format.
- Decision: Materialize computed online features into JSON documents under `data/features/online_bootstrap/` as the first local serving-store representation.
- Rationale: This keeps the streaming computation and retrieval contract explicit while avoiding premature infrastructure coupling.
- Consequences: T21 can read from this store first, and a later Redis-backed implementation should preserve the same logical feature names and payload shapes.

## [2026-04-01] D-011: Expose local online features through a service abstraction before adding an API layer
- Plan: v1.1
- Context: Inference code needs a stable way to fetch online features, but a dedicated HTTP serving surface would be premature before the recommendation-serving path is built.
- Options considered:
  - Read JSON files directly wherever features are needed.
  - Introduce a small service abstraction that owns lookup behavior over the local store.
- Decision: Add an `OnlineFeatureService` that reads the local store and exposes typed lookup methods for session, customer, and article features.
- Rationale: This keeps the retrieval interface stable while allowing the storage backend to change later without touching inference callers.
- Consequences: T32 can depend on the service abstraction instead of file paths, and a later Redis-backed implementation can swap in behind the same interface.

## [2026-04-01] D-012: Validate parity using explicitly mapped overlapping features
- Plan: v1.1
- Context: Offline and online feature sets are not identical, so parity checks need to compare only the fields whose semantics are intended to match.
- Options considered:
  - Compare every offline feature to every online feature.
  - Maintain an explicit mapping for the overlapping logical features and validate only those pairs.
- Decision: Use an explicit offline-to-online mapping for parity validation and keep freshness validation as a separate check.
- Rationale: This avoids false failures where offline-only or online-only features are expected to differ.
- Consequences: As the feature platform grows, new overlapping fields should be added to the mapping deliberately instead of assuming automatic parity.

## [2026-04-01] D-013: Use staged late fusion for multimodal retrieval evolution
- Plan: v1.1
- Context: The retrieval layer needs a credible multimodal path, but the project should still ship an inspectable first baseline before full fusion complexity arrives.
- Options considered:
  - Start directly with a tightly coupled multimodal encoder.
  - Start with text-first retrieval and evolve to late fusion over separate text and image embeddings.
- Decision: Use a staged strategy: text-first retrieval baseline first, then late-fusion multimodal retrieval while preserving unimodal artifacts.
- Rationale: This keeps the early pipeline simpler to debug and preserves fallback behavior when image coverage is incomplete.
- Consequences: T24 should generate unimodal embeddings separately and treat fused embeddings as an additional derived artifact rather than the only representation.

## [2026-04-01] D-014: Use deterministic hash-based local embeddings before introducing external model dependencies
- Plan: v1.1
- Context: T24 needs reusable embedding artifacts now, but the backend does not yet include model-serving dependencies or pretrained encoder weights.
- Options considered:
  - Add real embedding-model dependencies immediately.
  - Emit deterministic local embeddings from normalized text and image-manifest inputs first.
- Decision: Build the first embedding pipeline with deterministic hash-based encoders that generate text, image, and fused JSONL artifacts plus manifests.
- Rationale: This keeps the retrieval pipeline reproducible and testable, preserves the artifact boundaries needed for T25, and avoids premature dependency weight before the indexing and serving slices exist.
- Consequences: Later model-backed encoders should preserve the same artifact contract where practical so indexing and retrieval callers can evolve without a full pipeline rewrite.

## [2026-04-01] D-015: Use file-backed JSONL vector indexes before adding a vector database
- Plan: v1.1
- Context: T25 needs a rebuildable local index that T26 can query, but the project has not yet introduced Qdrant or Milvus into the runtime.
- Options considered:
  - Block indexing on an external vector database.
  - Materialize local index records from embedding artifacts first.
- Decision: Build text and fused vector indexes as JSONL records plus a manifest under `data/indexes/`.
- Rationale: This keeps index state inspectable, reproducible, and easy to rebuild while preserving the source-of-truth boundary at the embedding layer.
- Consequences: Later vector-database integration should consume the same embedding artifacts and preserve the logical collection boundaries for text and fused retrieval.

## [2026-04-01] D-016: Build retrieval queries from free text, seed items, and online-context tokens
- Plan: v1.1
- Context: T26 depends on both the vector index and the online feature-serving layer, but the project does not yet have learned user/query encoders.
- Options considered:
  - Restrict retrieval to text-only queries until learned encoders exist.
  - Combine hashed free-text payloads, seed-item vectors, and serialized online-feature context into one local query representation.
- Decision: The first candidate retriever builds the query representation from optional query text, optional seed article vectors, and available online session/customer feature tokens.
- Rationale: This gives the retrieval path a concrete request-context story now and creates a clean seam for later learned query encoders.
- Consequences: Future retrieval upgrades should be able to replace the query encoder while preserving the high-level request contract and candidate response shape.
