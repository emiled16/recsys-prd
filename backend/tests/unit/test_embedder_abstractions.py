from __future__ import annotations

import unittest

from recsys_prd.retrieval.embedders import (
    OpenClipImageEmbedder,
    SentenceTransformerTextEmbedder,
    TorchImageEmbedder,
    TorchTextEmbedder,
)


class FakeSentenceTransformerModel:
    def __init__(self) -> None:
        self.payloads: list[str] = []

    def encode(
        self,
        payloads: list[str],
        *,
        batch_size: int,
        normalize_embeddings: bool,
        show_progress_bar: bool,
    ) -> list[list[float]]:
        self.payloads = payloads
        return [[3.0, 4.0], [5.0, 12.0]]


class FakeOpenClipModel:
    def __init__(self) -> None:
        self.batches: list[list[str]] = []

    def encode_image(self, batch: list[str]) -> list[list[float]]:
        self.batches.append(batch)
        if batch == ["processed:/tmp/a.jpg", "processed:/tmp/b.jpg"]:
            return [[0.0, 2.0], [6.0, 8.0]]
        return [[1.0, 1.0] for _ in batch]


class EmbedderAbstractionTests(unittest.TestCase):
    def test_sentence_transformer_embedder_emits_text_records(self) -> None:
        model = FakeSentenceTransformerModel()
        embedder = SentenceTransformerTextEmbedder(
            model=model,
            model_name="sentence-transformers/test-model",
            model_version="test",
        )

        records = embedder.embed_articles(
            [
                {
                    "article_id": "1001",
                    "prod_name": "Summer Dress",
                    "product_type_name": "dress",
                    "product_group_name": "garment upper body",
                    "colour_group_name": "light beige",
                    "department_name": "Ladies Dresses",
                    "detail_desc": "airy cotton dress",
                    "image_path": "/tmp/a.jpg",
                },
                {
                    "article_id": "1002",
                    "prod_name": "Relaxed Tee",
                    "product_type_name": "t-shirt",
                    "product_group_name": "garment upper body",
                    "colour_group_name": "white",
                    "department_name": "Ladies Tops",
                    "detail_desc": "soft jersey tee",
                },
            ],
            generated_at="2026-04-02T00:00:00Z",
        )

        self.assertEqual(len(records), 2)
        self.assertIn("summer dress", model.payloads[0])
        self.assertEqual(records[0].article_id, "1001")
        self.assertEqual(records[0].vector_dimension, 2)
        self.assertAlmostEqual(records[0].vector[0], 0.6, places=5)
        self.assertTrue(records[0].modality_availability["image"])
        self.assertFalse(records[1].modality_availability["image"])

    def test_openclip_embedder_emits_image_records(self) -> None:
        model = FakeOpenClipModel()
        embedder = OpenClipImageEmbedder(
            model=model,
            preprocess=lambda path: f"processed:{path}",
            model_version="test",
            batch_size=2,
        )

        records = embedder.embed_images(
            [
                {
                    "article_id": "1001",
                    "image_path": "/tmp/a.jpg",
                    "department_name": "Ladies Dresses",
                },
                {
                    "article_id": "1002",
                    "image_path": "/tmp/b.jpg",
                    "department_name": "Ladies Tops",
                },
            ],
            generated_at="2026-04-02T00:00:00Z",
        )

        self.assertEqual(len(records), 2)
        self.assertEqual(model.batches, [["processed:/tmp/a.jpg", "processed:/tmp/b.jpg"]])
        self.assertEqual(records[0].source_path, "/tmp/a.jpg")
        self.assertEqual(records[1].vector_dimension, 2)
        self.assertAlmostEqual(records[1].vector[1], 0.8, places=5)

    def test_torch_projection_embedders_emit_lineage_metadata(self) -> None:
        text_embedder = TorchTextEmbedder(dimension=6, seed=7)
        image_embedder = TorchImageEmbedder(dimension=6, seed=11)

        text_records = text_embedder.embed_articles(
            [
                {
                    "article_id": "1001",
                    "prod_name": "Summer Dress",
                    "product_type_name": "dress",
                    "product_group_name": "garment upper body",
                    "colour_group_name": "light beige",
                    "department_name": "Ladies Dresses",
                    "detail_desc": "airy cotton dress",
                    "image_path": "/tmp/a.jpg",
                }
            ],
            generated_at="2026-04-02T00:00:00Z",
        )
        image_records = image_embedder.embed_images(
            [
                {
                    "article_id": "1001",
                    "image_path": "/tmp/a.jpg",
                    "department_name": "Ladies Dresses",
                }
            ],
            generated_at="2026-04-02T00:00:00Z",
        )

        self.assertEqual(text_records[0].backend, "torch_projection")
        self.assertIn("payload_digest", text_records[0].lineage)
        self.assertEqual(image_records[0].backend, "torch_projection")
        self.assertIn("projection_seed", image_records[0].lineage)


if __name__ == "__main__":
    unittest.main()
