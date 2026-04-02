from __future__ import annotations

import json
from typing import Any

from confluent_kafka import Consumer

from recsys_prd.config import AppSettings, get_app_settings
from recsys_prd.features.online_store import RedisOnlineFeatureStore
from recsys_prd.features.update_processor import FeatureUpdateProcessor
from recsys_prd.schemas.artifacts import FeatureStoreWriteRecord


def consume_feature_updates(
    settings: AppSettings | None = None,
    *,
    consumer: Any | None = None,
    store: RedisOnlineFeatureStore | None = None,
    processor: FeatureUpdateProcessor | None = None,
    max_messages: int | None = None,
) -> dict[str, Any]:
    """Consume broker events and persist online feature updates into Redis."""
    settings = settings or get_app_settings()
    consumer = consumer or Consumer(
        {
            "bootstrap.servers": settings.services.broker.bootstrap_servers,
            "group.id": "recsys-prd-feature-updates",
            "auto.offset.reset": "earliest",
        }
    )
    store = store or RedisOnlineFeatureStore(settings=settings)
    processor = processor or FeatureUpdateProcessor()
    consumer.subscribe(
        [
            settings.services.broker.interactions_topic,
            settings.services.broker.catalog_topic,
        ]
    )
    processed_count = 0
    write_count = 0
    while max_messages is None or processed_count < max_messages:
        message = consumer.poll(0.1)
        if message is None:
            if max_messages is None:
                continue
            break
        event = json.loads(message.value().decode("utf-8"))
        writes = processor.apply(event)
        for write in writes:
            _persist_write(store, write)
        processed_count += 1
        write_count += len(writes)
    consumer.close()
    return {"processed_messages": processed_count, "applied_writes": write_count}


def _persist_write(store: RedisOnlineFeatureStore, write: FeatureStoreWriteRecord) -> None:
    if write.entity_type == "session":
        customer_id, session_id = write.entity_key.split("::", maxsplit=1)
        store.put_session_features(customer_id, session_id, write.payload)
        return
    if write.entity_type == "customer":
        store.put_customer_features(write.entity_key, write.payload)
        return
    store.put_article_features(write.entity_key, write.payload)
