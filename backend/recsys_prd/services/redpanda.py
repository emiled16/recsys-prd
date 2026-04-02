from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from confluent_kafka import Consumer, Producer
from confluent_kafka.admin import AdminClient, NewTopic

from recsys_prd.config import AppSettings, get_app_settings
from recsys_prd.events.io import read_jsonl


def bootstrap_redpanda_topics(
    settings: AppSettings | None = None,
    *,
    admin_client: Any | None = None,
) -> dict[str, Any]:
    """Ensure the broker topics needed by replay and online updates exist."""
    settings = settings or get_app_settings()
    admin_client = admin_client or AdminClient(
        {"bootstrap.servers": settings.services.broker.bootstrap_servers}
    )
    topics = [
        settings.services.broker.interactions_topic,
        settings.services.broker.catalog_topic,
        "feature_updates",
        "exposure_events",
    ]
    new_topics = [NewTopic(topic, num_partitions=1, replication_factor=1) for topic in topics]
    futures = admin_client.create_topics(new_topics)
    created_topics = []
    for topic, future in futures.items():
        try:
            future.result()
            created_topics.append(topic)
        except Exception:
            # Keep broker bootstrap idempotent when topics already exist.
            created_topics.append(topic)
    return {
        "bootstrap_servers": settings.services.broker.bootstrap_servers,
        "topics": topics,
        "created_topics": created_topics,
    }


class KafkaReplayPublisher:
    """Publish replay artifacts to Kafka-compatible topics."""

    def __init__(
        self,
        settings: AppSettings | None = None,
        *,
        producer: Any | None = None,
    ) -> None:
        self.settings = settings or get_app_settings()
        self.producer = producer or Producer(
            {"bootstrap.servers": self.settings.services.broker.bootstrap_servers}
        )

    def publish(self, topic: str, events: list[dict[str, Any]]) -> dict[str, Any]:
        for event in events:
            key = event.get("article_id") or event.get("customer_id") or event["event_id"]
            self.producer.produce(
                topic,
                key=str(key),
                value=json.dumps(event).encode("utf-8"),
            )
        self.producer.flush()
        return {"topic": topic, "published_count": len(events)}

    def publish_manifest(self, manifest_path: Path) -> dict[str, Any]:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        outputs = {}
        for topic_name, topic_manifest in manifest["topics"].items():
            outputs[topic_name] = self.publish(topic_name, read_jsonl(Path(topic_manifest["path"])))
        return outputs


def validate_broker_replay(
    settings: AppSettings | None = None,
    *,
    manifest_path: Path,
    consumer: Any | None = None,
    timeout: float = 0.1,
) -> dict[str, Any]:
    """Validate broker delivery counts against a replay manifest."""
    settings = settings or get_app_settings()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    consumer = consumer or Consumer(
        {
            "bootstrap.servers": settings.services.broker.bootstrap_servers,
            "group.id": "recsys-prd-validation",
            "auto.offset.reset": "earliest",
        }
    )
    topics = list(manifest["topics"].keys())
    consumer.subscribe(topics)
    observed_counts = {topic: 0 for topic in topics}
    expected_counts = {
        topic: int(topic_manifest["row_count"])
        for topic, topic_manifest in manifest["topics"].items()
    }
    while any(observed_counts[topic] < expected_counts[topic] for topic in topics):
        message = consumer.poll(timeout)
        if message is None:
            break
        topic = message.topic()
        if topic in observed_counts:
            observed_counts[topic] += 1
    consumer.close()
    return {
        "ok": observed_counts == expected_counts,
        "expected_counts": expected_counts,
        "observed_counts": observed_counts,
    }
