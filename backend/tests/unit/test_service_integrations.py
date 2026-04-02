from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from recsys_prd.features.consumer import consume_feature_updates
from recsys_prd.features.online_service import OnlineFeatureService
from recsys_prd.features.online_store import RedisOnlineFeatureStore
from recsys_prd.features.update_processor import FeatureUpdateProcessor
from recsys_prd.services.mlflow_store import probe_mlflow_tracking
from recsys_prd.services.qdrant_store import QdrantIndexManager, ensure_qdrant_connection
from recsys_prd.services.redpanda import (
    KafkaReplayPublisher,
    bootstrap_redpanda_topics,
    validate_broker_replay,
)


class FakeRedisClient:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}

    def set(self, key: str, value: str) -> None:
        self.values[key] = value

    def get(self, key: str) -> str | None:
        return self.values.get(key)

    def ping(self) -> bool:
        return True


class FakeProducer:
    def __init__(self) -> None:
        self.messages: list[tuple[str, str, bytes]] = []

    def produce(self, topic: str, key: str, value: bytes) -> None:
        self.messages.append((topic, key, value))

    def flush(self) -> None:
        return None


class FakeTopicFuture:
    def result(self) -> None:
        return None


class FakeAdminClient:
    def create_topics(self, topics) -> dict[str, FakeTopicFuture]:
        return {topic.topic: FakeTopicFuture() for topic in topics}


class FakeMessage:
    def __init__(self, topic: str, value: dict[str, object]) -> None:
        self._topic = topic
        self._value = json.dumps(value).encode("utf-8")

    def topic(self) -> str:
        return self._topic

    def value(self) -> bytes:
        return self._value


class FakeConsumer:
    def __init__(self, messages: list[FakeMessage]) -> None:
        self.messages = messages

    def subscribe(self, topics) -> None:
        return None

    def poll(self, timeout: float):
        if self.messages:
            return self.messages.pop(0)
        return None

    def close(self) -> None:
        return None


class FakeCollection:
    def __init__(self, name: str) -> None:
        self.name = name


class FakeCollectionsResponse:
    def __init__(self, names: list[str]) -> None:
        self.collections = [FakeCollection(name) for name in names]


class FakeQdrantClient:
    def __init__(self) -> None:
        self.collections = ["existing"]
        self.upserts = []

    def get_collections(self):
        return FakeCollectionsResponse(self.collections)

    def create_collection(self, collection_name: str, vectors_config) -> None:
        self.collections.append(collection_name)

    def upsert(self, collection_name: str, points) -> None:
        self.upserts.append((collection_name, points))


class FakeRunInfo:
    def __init__(self, run_id: str) -> None:
        self.run_id = run_id


class FakeRun:
    def __init__(self, run_id: str) -> None:
        self.info = FakeRunInfo(run_id)


class FakeMlflowClient:
    def __init__(self) -> None:
        self.params = {}
        self.metrics = {}
        self.artifacts = []

    def create_run(self, experiment_id: str, tags: dict[str, str]):
        return FakeRun("run-123")

    def log_param(self, run_id: str, key: str, value) -> None:
        self.params[key] = value

    def log_metric(self, run_id: str, key: str, value: float) -> None:
        self.metrics[key] = value

    def log_artifact(self, run_id: str, path: str) -> None:
        self.artifacts.append(path)


class ServiceIntegrationTests(unittest.TestCase):
    def test_bootstraps_redpanda_topics(self) -> None:
        result = bootstrap_redpanda_topics(admin_client=FakeAdminClient())
        self.assertIn("interaction_events", result["topics"])

    def test_publishes_and_validates_replay_messages(self) -> None:
        producer = FakeProducer()
        publisher = KafkaReplayPublisher(producer=producer)
        with tempfile.TemporaryDirectory() as tmp_dir:
            manifest_path = Path(tmp_dir) / "manifest.json"
            events_path = Path(tmp_dir) / "events.jsonl"
            events = [{"event_id": "1", "customer_id": "c1"}]
            events_path.write_text(json.dumps(events[0]) + "\n", encoding="utf-8")
            manifest_path.write_text(
                json.dumps(
                    {
                        "topics": {
                            "interaction_events": {
                                "path": str(events_path),
                                "row_count": 1,
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )
            publisher.publish_manifest(manifest_path)
            self.assertEqual(len(producer.messages), 1)
            result = validate_broker_replay(
                manifest_path=manifest_path,
                consumer=FakeConsumer([FakeMessage("interaction_events", {"event_id": "1"})]),
            )
            self.assertTrue(result["ok"])

    def test_redis_store_and_online_service_round_trip(self) -> None:
        store = RedisOnlineFeatureStore(client=FakeRedisClient())
        store.put_customer_features("c1", {"purchase_count_30d_rt": 2})
        service = OnlineFeatureService(store=store)
        self.assertEqual(
            service.get_customer_realtime_features(customer_id="c1")["purchase_count_30d_rt"],
            2,
        )

    def test_feature_consumer_applies_broker_updates_to_store(self) -> None:
        store = RedisOnlineFeatureStore(client=FakeRedisClient())
        event = {
            "event_id": "evt-1",
            "event_type": "purchase",
            "event_time": "2020-09-20T00:00:00Z",
            "customer_id": "0001",
            "session_id": "0001-2020-09-20",
            "article_id": "108775015",
            "price": "29.99",
        }
        result = consume_feature_updates(
            consumer=FakeConsumer([FakeMessage("interaction_events", event)]),
            store=store,
            processor=FeatureUpdateProcessor(),
            max_messages=1,
        )
        self.assertEqual(result["applied_writes"], 2)
        self.assertEqual(
            store.get_customer_features("0001")["purchase_count_30d_rt"],
            1,
        )

    def test_qdrant_probe_and_upsert_use_manager(self) -> None:
        client = FakeQdrantClient()
        result = ensure_qdrant_connection(client=client)
        manager = QdrantIndexManager(client=client)
        upserted = manager.upsert(
            "article_text_embeddings",
            [
                {
                    "article_id": "1",
                    "vector": [0.1, 0.2],
                    "structured_metadata": {"department_name": "ladies"},
                    "modality_availability": {"text": True},
                    "model_name": "m",
                    "model_version": "v1",
                }
            ],
        )
        self.assertIn("article_text_embeddings", result["managed_collections"])
        self.assertEqual(upserted, 1)

    def test_mlflow_probe_logs_a_run(self) -> None:
        result = probe_mlflow_tracking(client=FakeMlflowClient())
        self.assertEqual(result["run_id"], "run-123")
