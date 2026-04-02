from __future__ import annotations

import unittest

from recsys_prd.schemas.artifacts import (
    EmbeddingArtifactRecord,
    ModelRegistrationRecord,
    ReplayBatchManifest,
    ReplayTopicManifest,
)


class ArtifactSchemaTests(unittest.TestCase):
    def test_replay_batch_manifest_validates_nested_topics(self) -> None:
        manifest = ReplayBatchManifest(
            generated_at_utc="2026-04-02T00:00:00Z",
            topics={"interaction_events": ReplayTopicManifest(path="/tmp/a.jsonl", row_count=2)},
        )

        self.assertEqual(manifest.topics["interaction_events"].row_count, 2)

    def test_embedding_record_sets_vector_dimension(self) -> None:
        record = EmbeddingArtifactRecord(
            article_id="1",
            generated_at_utc="2026-04-02T00:00:00Z",
            model_name="model",
            model_version="v1",
            modality="text",
            strategy_name="baseline",
            vector=[0.1, 0.2],
            vector_dimension=2,
            structured_metadata={"department_name": "Ladieswear"},
            modality_availability={"text": True, "image": False},
        )

        self.assertEqual(record.vector_dimension, 2)

    def test_model_registration_record_captures_lineage(self) -> None:
        record = ModelRegistrationRecord(
            registration_id="model::run-1",
            registered_at_utc="2026-04-02T00:00:00Z",
            model_name="ranker",
            model_version="v1",
            stage="candidate",
            source_run_id="run-1",
            training_manifest_path="/tmp/manifest.json",
            dataset={"path": "/tmp/dataset.parquet"},
            training_config={"epochs": 3},
            metrics={"auc": 0.9},
            artifacts={"model_path": "/tmp/model.json"},
            lineage={"training_dataset_path": "/tmp/dataset.parquet"},
            registration_path="/tmp/registration.json",
        )

        self.assertEqual(record.lineage["training_dataset_path"], "/tmp/dataset.parquet")
