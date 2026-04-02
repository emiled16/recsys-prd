# Multimodal Representation Strategy

## Purpose
This document defines how product text, images, and structured attributes are represented and combined for retrieval-ready embeddings.

The strategy is intentionally staged so the first implementation can ship usable retrieval artifacts without locking the project into an overly complex fusion architecture too early.

## Representation Goals
- preserve strong semantic coverage from product text
- use image embeddings to recover visual similarity not captured by taxonomy fields
- retain structured catalog attributes as interpretable side information
- support both retrieval and downstream ranking reuse

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
  - modality availability flags
  - generation timestamp

## Acceptance Criteria
- The modality boundaries and fusion strategy are explicit.
- The strategy is concrete enough to drive embedding generation in `T24` and indexing in `T25`.
