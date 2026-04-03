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

## [2026-04-02] D-017: Generate ranking training rows with observed positives plus retrieval negatives
- Plan: v1.1
- Context: T27 needs ranking examples that reflect the retrieval stage while preserving leakage-safe feature semantics from T18.
- Options considered:
  - Sample negatives independently of retrieval and join features afterward.
  - Use retrieved candidates as negatives and compute every candidate row from pre-label historical state.
- Decision: Build ranking datasets with one observed positive row per transaction plus deterministic negatives drawn from the retrieval index, and compute candidate features against history strictly before the label time.
- Rationale: This keeps training data aligned with the real candidate-generation path while preserving point-in-time correctness for both positives and negatives.
- Consequences: Future ranking-training work should treat retrieval score and candidate-source metadata as first-class inputs and preserve the same leakage boundary if the retriever changes.

## [2026-04-02] D-018: Start ranking training with a deterministic linear baseline before introducing deep ranking models
- Plan: v1.1
- Context: T28 needs reproducible training artifacts now, but the project has not yet introduced a tensor stack, experiment service, or the evaluation framework that would justify a heavier ranking model.
- Options considered:
  - Add a neural ranking model and larger ML dependencies immediately.
  - Start with a deterministic linear baseline over the ranking dataset and preserve clean artifact boundaries for later upgrades.
- Decision: Train the first ranking model as a deterministic logistic baseline over numeric and hashed categorical ranking features, with serialized weights, metrics, and tracked run manifests.
- Rationale: This creates a concrete training workflow and inspectable model artifact now while preserving a clean migration path toward richer ranking models later.
- Consequences: T29 and T31 should treat the saved model artifact and run metadata as the stable interface, even if the internal trainer later moves to MLflow and deeper architectures.

## [2026-04-02] D-019: Register promoted local models through a file-backed candidate registry before adding MLflow
- Plan: v1.1
- Context: T29 needs model versioning and lineage now, but the stack has not yet introduced the external tracking and registry services named in the long-term system design.
- Options considered:
  - Block model registration on MLflow integration.
  - Create a lightweight local registry that records candidate versions, pointers, metrics, and lineage from training artifacts.
- Decision: Register candidate ranking models into a file-backed local registry under `data/models/registry/`, with append-only history and a `latest_candidate` pointer per model family.
- Rationale: This gives downstream evaluation and serving code a stable promoted-model reference without forcing early infrastructure dependencies.
- Consequences: Future MLflow-backed registration should preserve the same logical fields for run ID, artifact paths, metrics, and stage transitions so local callers do not need a second contract.

## [2026-04-02] D-020: Separate runtime ownership across backend, orchestration, and infra surfaces
- Plan: v1.6
- Context: The repository had both a top-level Dagster scaffold and backend-owned Dagster code, while local shared services still appeared as a repo-root concern.
- Options considered:
  - Keep Dagster definitions and local broker bootstrap inside the backend package.
  - Split runtime ownership so backend, orchestration, and infra each own only their direct runtime surface.
- Decision: Make `backend/` own API and integration logic only, `orchestration/` own Dagster user code and runtime commands, and `infra/local/` own Docker Compose, env defaults, and shared-service bootstrap helpers.
- Rationale: This removes backend-internal ownership of shared runtimes, makes local development boundaries explicit, and aligns the repository with a production-like deployment topology.
- Consequences: Local run commands change, backend defaults must target externally reachable service endpoints, and Dagster code should no longer live under `backend/recsys_prd/`.

## [2026-04-02] D-021: Treat the repo-root Docker Compose file as a compatibility entrypoint only
- Plan: v1.6
- Context: Existing workflows referenced `docker-compose.yml` at the repository root, but M1 requires `infra/local/` to become the canonical owner of shared local services.
- Options considered:
  - Keep the full service manifest at the root.
  - Move the canonical manifest into `infra/local/` and leave a thin root entrypoint for compatibility.
- Decision: Store the canonical shared-service Compose manifest at `infra/local/docker-compose.yml` and reduce the root `docker-compose.yml` to a compatibility include.
- Rationale: This preserves an obvious repo-root entrypoint while making ownership and future infra expansion explicit.
- Consequences: New docs and scripts should reference `infra/local/` directly, and compatibility behavior now depends on Compose include support.

## [2026-04-02] D-022: Expand the public API surface to support realistic local application tests
- Plan: v1.6
- Context: Local testing needed more than `POST /recommendations`; frontend and smoke-test flows also require readiness, diagnostics, and public event tracking.
- Options considered:
  - Keep a minimal API and continue testing through internal module calls.
  - Publish a small but explicit application-facing contract for health, readiness, diagnostics, recommendations, and tracking events.
- Decision: Standardize on `/healthz`, `/readyz`, `/diagnostics`, `/recommendations`, `/events`, and `/metrics` as the public local application contract.
- Rationale: This makes application-level validation realistic while keeping unsafe internal state out of the API.
- Consequences: Frontend, smoke tests, and orchestration checks should depend on these public endpoints instead of importing backend modules directly.

## [2026-04-02] D-023: Run the frontend outside Compose with Vite and a fetch-based client layer
- Plan: v1.6
- Context: Local iteration on the browser surface should be fast and should not imply that the frontend belongs inside the infra-owned Docker Compose stack.
- Options considered:
  - Run the frontend from Docker Compose and standardize on Axios.
  - Run the frontend directly with Vite and use the browser `fetch` API or a minimal wrapper.
- Decision: Add a top-level `frontend/` workspace with Vite for local development and a thin `fetch`-based HTTP client layer.
- Rationale: This keeps the browser feedback loop fast, reduces client dependencies, and respects the ownership split between application code and shared infra.
- Consequences: Local runbooks must treat frontend, backend, orchestration, and shared services as separate processes.

## [2026-04-02] D-024: Package deployment surfaces independently with Helm overlays per environment
- Plan: v1.6
- Context: The production-like topology needs backend API, frontend, orchestration, simulator jobs, and pipelines jobs to remain distinct deployable surfaces.
- Options considered:
  - Package the platform as one backend-centric Helm chart.
  - Create a chart per top-level runtime plus environment overlays that describe shared-service ownership.
- Decision: Use `infra/helm/` to define independent charts and environment-specific overlays for local, demo, and production-like targets.
- Rationale: This keeps deployment packaging aligned with the repository boundary decisions and avoids hiding ownership under one monolithic release.
- Consequences: Shared dependencies such as Kafka, Redis, Qdrant, MLflow, and observability must be documented as external or platform-managed per environment.

## [2026-04-02] D-025: Standardize the local embedding path on a PyTorch-backed projection contract
- Plan: v1.6
- Context: The earlier deterministic hashing path was useful for bootstrap work, but the next retrieval phase needed a production-shaped artifact contract with explicit runtime metadata and lineage.
- Options considered:
  - Keep the hash-only embedding implementation as the canonical path.
  - Move to a PyTorch-backed local embedding contract while preserving deterministic fallback behavior when the dependency is absent.
- Decision: Treat the retrieval embedding stage as a PyTorch-backed projection pipeline with explicit runtime metadata, dataset digests, and per-record lineage, while allowing deterministic fallback projection when `torch` is unavailable.
- Rationale: This preserves reproducibility and testability locally while making the embedding artifacts look and behave more like real production outputs.
- Consequences: Embedding manifests and downstream index manifests must now include backend/runtime metadata and lineage digests.

## [2026-04-02] D-026: Gate promotion on offline quality, API smoke checks, and online guardrails together
- Plan: v1.6
- Context: Candidate registration alone is not a credible promotion model once retrieval evaluation, experimentation, and public API checks exist.
- Options considered:
  - Promote the latest run after registration only.
  - Require retrieval readiness, ranking evaluation thresholds, public API smoke checks, and online guardrail status before promotion.
- Decision: Add a promotion-gate report that combines retrieval readiness, ranking metrics, API smoke results, and online evaluation guardrails into one decision artifact.
- Rationale: This gives orchestration and future deployment steps one consistent source of truth for promotion eligibility.
- Consequences: Dagster evaluation and promotion jobs must produce or consume the gate report instead of inferring readiness from a single model artifact.

## [2026-04-02] D-027: Standardize offline pipeline execution on Spark while keeping serving paths dependency-light
- Plan: v1.7
- Context: The repository already split top-level runtime surfaces, but offline normalization and validation still behave like lightweight in-process Python jobs even though they are pipeline concerns. The next stage needs a clearer compute boundary for batch work without pulling Spark into the serving runtime.
- Options considered:
  - Keep offline jobs on ad hoc in-process Python implementations.
  - Standardize normalization, validation, and training-set preparation on `pyspark` with lazy imports so serving code remains unaffected.
- Decision: Treat Spark as the default execution runtime for offline pipeline stages, configured through `RECSYS_PRD_SPARK_*` settings and initialized only inside pipeline-owned modules.
- Rationale: This creates a real batch-compute boundary for offline work, makes later scale-up easier, and keeps the FastAPI/backend surface free from eager Spark runtime coupling.
- Consequences:
  - Pipeline modules need shared Spark session helpers and Spark-owned dataset IO entrypoints.
  - Spark jobs must preserve the existing artifact contract under `data/normalized/`, `data/features/offline/`, and `data/models/training_sets/`.
  - Parity checks must compare Spark outputs against the pre-Spark outputs for row counts, required fields, key uniqueness, and timestamp normalization before legacy code paths are removed.
  - Backend serving code must not import `pyspark` or initialize Spark sessions.
