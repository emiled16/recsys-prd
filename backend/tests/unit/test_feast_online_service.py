from __future__ import annotations

import unittest

from recsys_prd.features.feast_online_service import FeastOnlineFeatureService


class FakeOnlineResponse:
    def __init__(self, payload: dict[str, list[object]]) -> None:
        self.payload = payload

    def to_dict(self) -> dict[str, list[object]]:
        return self.payload


class FakeFeastStore:
    def __init__(self) -> None:
        self.calls: list[tuple[list[str], list[dict[str, str]]]] = []

    def get_online_features(
        self,
        *,
        features: list[str],
        entity_rows: list[dict[str, str]],
    ) -> FakeOnlineResponse:
        self.calls.append((features, entity_rows))
        if features[0].startswith("session_intent_features:"):
            return FakeOnlineResponse(
                {
                    "recent_search_terms": ["linen dress"],
                    "cart_add_count_30m": ["2"],
                }
            )
        return FakeOnlineResponse(
            {
                "purchase_count_30d_rt": ["4"],
                "purchase_count_7d_rt": ["1"],
            }
        )


class FeastOnlineFeatureServiceTests(unittest.TestCase):
    def test_fetches_session_and_customer_features_from_feast(self) -> None:
        store = FakeFeastStore()
        service = FeastOnlineFeatureService(store=store)

        session_payload = service.get_session_intent_features(
            customer_id="0001",
            session_id="session-1",
        )
        customer_payload = service.get_customer_realtime_features(customer_id="0001")

        self.assertEqual(session_payload["recent_search_terms"], "linen dress")
        self.assertEqual(customer_payload["purchase_count_30d_rt"], "4")
        self.assertEqual(
            store.calls[0][1],
            [{"customer_session_id": "0001::session-1"}],
        )
        self.assertEqual(store.calls[1][1], [{"customer_id": "0001"}])


if __name__ == "__main__":
    unittest.main()
