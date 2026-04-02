from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModalitySpec:
    name: str
    input_fields: tuple[str, ...]
    output_artifact: str
    description: str


@dataclass(frozen=True)
class FusionStrategy:
    name: str
    stage: str
    required_modalities: tuple[str, ...]
    output_artifact: str
    description: str
