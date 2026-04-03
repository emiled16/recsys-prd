from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ImportError:  # pragma: no cover - fallback for environments missing pydantic-settings.
    BaseSettings = BaseModel
    SettingsConfigDict = dict


def _default_backend_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _default_project_root() -> Path:
    return _default_backend_root().parent


def _resolve_path(env_key: str, default: Path) -> Path:
    raw_value = os.getenv(env_key, "").strip()
    if not raw_value:
        return default
    return Path(raw_value).expanduser().resolve()


class PathSettings(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    project_root: Path = Field(default_factory=_default_project_root)
    backend_root: Path = Field(default_factory=_default_backend_root)
    data_root: Path | None = None
    raw_hm_root: Path | None = None
    normalized_root: Path | None = None
    reports_root: Path | None = None
    events_root: Path | None = None
    features_root: Path | None = None
    features_offline_root: Path | None = None
    online_feature_store_root: Path | None = None
    embeddings_root: Path | None = None
    indexes_root: Path | None = None
    models_root: Path | None = None
    feast_repo_root: Path | None = None

    def model_post_init(self, __context: object) -> None:
        data_root = self.data_root or self.project_root / "data"
        self.data_root = data_root
        self.raw_hm_root = self.raw_hm_root or data_root / "raw" / "hm"
        self.normalized_root = self.normalized_root or data_root / "normalized"
        self.reports_root = self.reports_root or data_root / "reports"
        self.events_root = self.events_root or data_root / "events"
        self.features_root = self.features_root or data_root / "features"
        self.features_offline_root = self.features_offline_root or self.features_root / "offline"
        self.online_feature_store_root = (
            self.online_feature_store_root or self.features_root / "online_bootstrap"
        )
        self.embeddings_root = self.embeddings_root or data_root / "embeddings"
        self.indexes_root = self.indexes_root or data_root / "indexes"
        self.models_root = self.models_root or data_root / "models"
        self.feast_repo_root = self.feast_repo_root or self.backend_root / "feast_repo"

    @classmethod
    def from_env(cls) -> PathSettings:
        project_root = _resolve_path("RECSYS_PRD_PROJECT_ROOT", _default_project_root())
        backend_root = _resolve_path("RECSYS_PRD_BACKEND_ROOT", project_root / "backend")
        data_root = _resolve_path("RECSYS_PRD_DATA_ROOT", project_root / "data")
        return cls(
            project_root=project_root,
            backend_root=backend_root,
            data_root=data_root,
            raw_hm_root=_resolve_path("RECSYS_PRD_RAW_HM_ROOT", data_root / "raw" / "hm"),
            normalized_root=_resolve_path("RECSYS_PRD_NORMALIZED_ROOT", data_root / "normalized"),
            reports_root=_resolve_path("RECSYS_PRD_REPORTS_ROOT", data_root / "reports"),
            events_root=_resolve_path("RECSYS_PRD_EVENTS_ROOT", data_root / "events"),
            features_root=_resolve_path("RECSYS_PRD_FEATURES_ROOT", data_root / "features"),
            features_offline_root=_resolve_path(
                "RECSYS_PRD_FEATURES_OFFLINE_ROOT",
                data_root / "features" / "offline",
            ),
            online_feature_store_root=_resolve_path(
                "RECSYS_PRD_ONLINE_FEATURE_STORE_ROOT",
                data_root / "features" / "online_bootstrap",
            ),
            embeddings_root=_resolve_path("RECSYS_PRD_EMBEDDINGS_ROOT", data_root / "embeddings"),
            indexes_root=_resolve_path("RECSYS_PRD_INDEXES_ROOT", data_root / "indexes"),
            models_root=_resolve_path("RECSYS_PRD_MODELS_ROOT", data_root / "models"),
            feast_repo_root=_resolve_path(
                "RECSYS_PRD_FEAST_REPO_ROOT",
                backend_root / "feast_repo",
            ),
        )


class RedisSettings(BaseModel):
    host: str = "127.0.0.1"
    port: int = 6379
    db: int = 0

    @property
    def url(self) -> str:
        return f"redis://{self.host}:{self.port}/{self.db}"


class BrokerSettings(BaseModel):
    bootstrap_servers: str = "127.0.0.1:9092"
    interactions_topic: str = "interaction_events"
    catalog_topic: str = "catalog_events"


class QdrantSettings(BaseModel):
    host: str = "127.0.0.1"
    port: int = 6333
    text_collection: str = "article_text_embeddings"
    fused_collection: str = "article_fused_embeddings"

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}"


class MLflowSettings(BaseModel):
    tracking_uri: str = "http://127.0.0.1:5001"
    artifact_root: str = "./data/mlflow"


class SparkSettings(BaseModel):
    app_name: str = "recsys-prd-pipelines"
    master: str = "local[*]"
    warehouse_dir: str = "data/_spark/warehouse"
    driver_bind_address: str = "127.0.0.1"
    ui_enabled: bool = False
    shuffle_partitions: int = 8

    @classmethod
    def from_env(cls) -> SparkSettings:
        return cls(
            app_name=os.getenv(
                "RECSYS_PRD_SPARK_APP_NAME",
                SparkSettings.model_fields["app_name"].default,
            ),
            master=os.getenv(
                "RECSYS_PRD_SPARK_MASTER",
                SparkSettings.model_fields["master"].default,
            ),
            warehouse_dir=os.getenv(
                "RECSYS_PRD_SPARK_WAREHOUSE_DIR",
                SparkSettings.model_fields["warehouse_dir"].default,
            ),
            driver_bind_address=os.getenv(
                "RECSYS_PRD_SPARK_DRIVER_BIND_ADDRESS",
                SparkSettings.model_fields["driver_bind_address"].default,
            ),
            ui_enabled=os.getenv("RECSYS_PRD_SPARK_UI_ENABLED", "false").lower() == "true",
            shuffle_partitions=int(
                os.getenv(
                    "RECSYS_PRD_SPARK_SHUFFLE_PARTITIONS",
                    SparkSettings.model_fields["shuffle_partitions"].default,
                )
            ),
        )


class ServiceSettings(BaseModel):
    broker: BrokerSettings = Field(default_factory=BrokerSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    qdrant: QdrantSettings = Field(default_factory=QdrantSettings)
    mlflow: MLflowSettings = Field(default_factory=MLflowSettings)

    @classmethod
    def from_env(cls) -> ServiceSettings:
        return cls(
            broker=BrokerSettings(
                bootstrap_servers=os.getenv(
                    "RECSYS_PRD_BROKER_BOOTSTRAP_SERVERS",
                    BrokerSettings.model_fields["bootstrap_servers"].default,
                ),
                interactions_topic=os.getenv(
                    "RECSYS_PRD_BROKER_INTERACTIONS_TOPIC",
                    BrokerSettings.model_fields["interactions_topic"].default,
                ),
                catalog_topic=os.getenv(
                    "RECSYS_PRD_BROKER_CATALOG_TOPIC",
                    BrokerSettings.model_fields["catalog_topic"].default,
                ),
            ),
            redis=RedisSettings(
                host=os.getenv("RECSYS_PRD_REDIS_HOST", RedisSettings.model_fields["host"].default),
                port=int(
                    os.getenv("RECSYS_PRD_REDIS_PORT", RedisSettings.model_fields["port"].default)
                ),
                db=int(os.getenv("RECSYS_PRD_REDIS_DB", RedisSettings.model_fields["db"].default)),
            ),
            qdrant=QdrantSettings(
                host=os.getenv(
                    "RECSYS_PRD_QDRANT_HOST",
                    QdrantSettings.model_fields["host"].default,
                ),
                port=int(
                    os.getenv("RECSYS_PRD_QDRANT_PORT", QdrantSettings.model_fields["port"].default)
                ),
                text_collection=os.getenv(
                    "RECSYS_PRD_QDRANT_TEXT_COLLECTION",
                    QdrantSettings.model_fields["text_collection"].default,
                ),
                fused_collection=os.getenv(
                    "RECSYS_PRD_QDRANT_FUSED_COLLECTION",
                    QdrantSettings.model_fields["fused_collection"].default,
                ),
            ),
            mlflow=MLflowSettings(
                tracking_uri=os.getenv(
                    "RECSYS_PRD_MLFLOW_TRACKING_URI",
                    MLflowSettings.model_fields["tracking_uri"].default,
                ),
                artifact_root=os.getenv(
                    "RECSYS_PRD_MLFLOW_ARTIFACT_ROOT",
                    MLflowSettings.model_fields["artifact_root"].default,
                ),
            ),
        )


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="RECSYS_PRD_",
        extra="ignore",
    )

    environment: str = "local"
    paths: PathSettings = Field(default_factory=PathSettings.from_env)
    services: ServiceSettings = Field(default_factory=ServiceSettings.from_env)
    spark: SparkSettings = Field(default_factory=SparkSettings.from_env)


@lru_cache(maxsize=1)
def get_app_settings() -> AppSettings:
    return AppSettings()
