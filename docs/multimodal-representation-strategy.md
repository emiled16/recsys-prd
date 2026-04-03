# Multimodal Representation Strategy

## Purpose
This document defines how product text, images, and structured attributes are represented and
combined for retrieval-ready embeddings.

The strategy is intentionally staged so the first implementation can ship usable retrieval artifacts without locking the project into an overly complex fusion architecture too early.

## Representation Goals
- preserve strong semantic coverage from product text
- use image embeddings to recover visual similarity not captured by taxonomy fields
- retain structured catalog attributes as interpretable side information
- support both retrieval and downstream ranking reuse
- keep embedding rebuilds reproducible through explicit manifests, model metadata, and dataset digests

## Production-Like Embedding Contract

The retrieval stack now standardizes on a PyTorch-backed local projection path that behaves like a
real embedding pipeline even when heavyweight pretrained weights are not installed in the workspace.

### Default Local Model Choices
- Text:
  - logical model name: `torch_text_projection`
  - version: `v1`
  - default seed: `13`
- Image:
  - logical model name: `torch_image_projection`
  - version: `v1`
  - default seed: `29`
- Fusion:
  - late fusion over normalized text and image vectors
  - lineage references to the upstream text and image artifact digests

### Runtime Behavior
- If `torch` is installed, vector projection uses a torch-backed matrix projection and normalization
  path.
- If `torch` is not installed, the same logical models fall back to a deterministic projection path
  so manifests and tests remain reproducible.
- The artifact contract records whether torch was available at build time.

### Reproducibility Requirements
- Persist dataset digests, normalized-root references, and generation timestamps in the embedding
  manifest.
- Record model name, model version, backend, projection seed, and per-record lineage digests.
- Preserve separate text, image, and fused artifacts so downstream evaluation can measure modality
  contribution and slice behavior.
- Treat vector index rebuilds as derivatives that point back to a specific embedding manifest.

## Product-Side Modalities

### Text Representation
- Inputs:
  - `prod_name`
  - `product_type_name`
  - `product_group_name`
  - `colour_group_name`
  - `department_name`
  - `detail_desc`
- Output:
  - dense text embedding per article
- Role:
  - primary semantic representation for retrieval cold start and query matching

### Image Representation
- Inputs:
  - product image files from `product_images_manifest`
- Output:
  - dense image embedding per article image
- Role:
  - visual similarity signal for style, silhouette, and color relationships

### Structured Representation
- Inputs:
  - normalized categorical attributes from `products_normalized`
  - selected static feature fields from `article_catalog_features`
- Output:
  - compact structured feature vector or encoded metadata bundle
- Role:
  - interpretable side channel for filtering, reranking, and late fusion

## Retrieval Strategy

### Stage 1: Text-First Retrieval Baseline
- Build one canonical text embedding per article.
- Attach structured metadata alongside the vector record.
- Use image embeddings offline for analysis and future fusion, but do not require them for the first retrieval index.

### Stage 2: Late-Fusion Multimodal Retrieval
- Maintain text and image embeddings as separate modality outputs.
- Produce one fused retrieval vector per article by combining text and image embeddings.
- Keep the unimodal embeddings for diagnostics and ablations.

### Stage 3: Query-Side Multimodality
- Support user/session embeddings informed by:
  - recent viewed or clicked items
  - recent search terms
  - optional image-conditioned query flows if the frontend later supports them

## Fusion Policy
- Default fusion style:
  - late fusion over independently computed text and image embeddings
- Why:
  - simpler to debug than end-to-end joint encoders
  - preserves unimodal fallbacks when an image is missing
  - supports modality ablation during evaluation

## Missing-Modality Policy
- If an article has no image, use text plus structured metadata only.
- If text description is sparse, keep the article eligible using title, category, and image inputs.
- The embedding pipeline must record modality availability in metadata.

## Storage Expectations
- Store text, image, and fused embeddings separately under:
  - `data/embeddings/text/`
  - `data/embeddings/image/`
  - `data/embeddings/fused/`
- Persist metadata with:
  - `article_id`
  - model name
  - model version
  - backend runtime
  - modality availability flags
  - generation timestamp
  - lineage digest and source dataset digest

## Evaluation and Monitoring Expectations
- Offline retrieval evaluation must emit global metrics plus slice metrics for image availability,
  query-length buckets, and department-level behavior.
- Promotion readiness should consider freshness of both embedding manifests and vector index
  manifests.
- Online monitoring should track fallback rate, null-result rate, and rollback recommendations
  derived from exposure and event logs.

## Acceptance Criteria
- The modality boundaries and fusion strategy are explicit.
- The strategy is concrete enough to drive embedding generation in `T24` and indexing in `T25`.
