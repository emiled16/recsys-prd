from __future__ import annotations

import unittest

from recsys_prd.retrieval.representation_strategy import fusion_strategies, modality_specs


class RepresentationStrategyTests(unittest.TestCase):
    def test_modality_specs_cover_text_image_and_structured_inputs(self) -> None:
        modalities = {item.name: item for item in modality_specs()}
        self.assertEqual(set(modalities.keys()), {"text", "image", "structured"})
        self.assertIn("detail_desc", modalities["text"].input_fields)
        self.assertEqual(modalities["image"].input_fields, ("image_path",))

    def test_fusion_strategy_is_staged(self) -> None:
        strategies = {item.name: item for item in fusion_strategies()}
        self.assertEqual(strategies["text_first_baseline"].stage, "stage_1")
        self.assertEqual(strategies["late_fusion_multimodal"].stage, "stage_2")


if __name__ == "__main__":
    unittest.main()
