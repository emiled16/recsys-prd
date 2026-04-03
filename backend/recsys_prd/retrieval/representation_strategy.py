from __future__ import annotations

from recsys_prd.retrieval.contracts import FusionStrategy, ModalitySpec

TEXT_MODALITY = ModalitySpec(
    name="text",
    input_fields=(
        "prod_name",
        "product_type_name",
        "product_group_name",
        "colour_group_name",
        "department_name",
        "detail_desc",
    ),
    output_artifact="text_article_embedding",
    description="Primary semantic article representation built from normalized text fields.",
)

IMAGE_MODALITY = ModalitySpec(
    name="image",
    input_fields=("image_path",),
    output_artifact="image_article_embedding",
    description="Visual article representation built from catalog imagery.",
)

STRUCTURED_MODALITY = ModalitySpec(
    name="structured",
    input_fields=(
        "product_type_name",
        "product_group_name",
        "colour_group_name",
        "department_name",
        "index_group_name",
    ),
    output_artifact="structured_article_features",
    description="Interpretable structured side information attached to retrieval records.",
)

TEXT_FIRST_BASELINE = FusionStrategy(
    name="text_first_baseline",
    stage="stage_1",
    required_modalities=("text", "structured"),
    output_artifact="text_retrieval_vector",
    description="Text-first retrieval with structured metadata attached to the vector record.",
)

LATE_FUSION_MULTIMODAL = FusionStrategy(
    name="late_fusion_multimodal",
    stage="stage_2",
    required_modalities=("text", "image", "structured"),
    output_artifact="fused_retrieval_vector",
    description="Late-fusion retrieval vector that preserves unimodal artifacts for diagnostics.",
)


def modality_specs() -> list[ModalitySpec]:
    """Return retrieval modality specifications in registry order."""
    return [TEXT_MODALITY, IMAGE_MODALITY, STRUCTURED_MODALITY]


def fusion_strategies() -> list[FusionStrategy]:
    """Return the staged retrieval fusion strategies."""
    return [TEXT_FIRST_BASELINE, LATE_FUSION_MULTIMODAL]
