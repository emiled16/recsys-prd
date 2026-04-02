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
