from __future__ import annotations

import unittest

from recsys_prd.schemas.artifacts import (
    EmbeddingArtifactManifest,
    EmbeddingArtifactRecord,
    ModelRegistrationRecord,
    PromotionReadinessReport,
    ReplayBatchManifest,
    ReplayTopicManifest,
    RetrievalEvaluationReport,
    RetrievalSliceMetric,
    VectorIndexArtifactManifest,
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
            backend="torch_projection",
            modality="text",
            strategy_name="baseline",
            vector=[0.1, 0.2],
            vector_dimension=2,
            structured_metadata={"department_name": "Ladieswear"},
            modality_availability={"text": True, "image": False},
        )

        self.assertEqual(record.vector_dimension, 2)

    def test_embedding_manifest_tracks_lineage(self) -> None:
        manifest = EmbeddingArtifactManifest(
            path="/tmp/embeddings.jsonl",
            row_count=2,
            model_name="torch_text_projection",
            model_version="v1",
            backend="torch_projection",
            strategy_name="text_first_baseline",
            required_modalities=["text", "structured"],
            dimension=12,
            artifact_digest="abc123",
            lineage={"source_digest": "source-123"},
        )

        self.assertEqual(manifest.lineage["source_digest"], "source-123")

    def test_vector_index_manifest_tracks_source_embedding_lineage(self) -> None:
        manifest = VectorIndexArtifactManifest(
            path="/tmp/index.jsonl",
            source_embedding_path="/tmp/embeddings.jsonl",
            source_embedding_manifest_path="/tmp/embeddings/manifest.json",
            row_count=2,
            dimension=12,
            strategy_name="text_first_baseline",
            artifact_digest="abc123",
            lineage={"source_embedding_digest": "digest-1"},
        )

        self.assertEqual(manifest.source_embedding_manifest_path, "/tmp/embeddings/manifest.json")

    def test_retrieval_evaluation_report_carries_readiness_summary(self) -> None:
        report = RetrievalEvaluationReport(
            evaluated_at_utc="2026-04-02T00:00:00Z",
            query_count=2,
            k=10,
            index_name="fused",
            metrics={"recall_at_k": 1.0},
            slices={
                "target_has_image=True": RetrievalSliceMetric(
                    slice_name="target_has_image=True", query_count=1, metrics={"recall_at_k": 1.0}
                )
            },
            freshness={"index_manifest_available": True},
            readiness=PromotionReadinessReport(ready_for_promotion=True),
        )

        self.assertTrue(report.readiness.ready_for_promotion)

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
