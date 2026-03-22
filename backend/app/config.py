from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import os


ROOT_DIR = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    service_name: str = "knowledge-steward-backend"
    version: str = "0.1.0"
    host: str = os.getenv("KS_HOST", "127.0.0.1")
    port: int = int(os.getenv("KS_PORT", "8787"))
    default_model_provider: str = os.getenv("KS_DEFAULT_MODEL_PROVIDER", "cloud")
    cloud_provider_name: str = os.getenv("KS_CLOUD_PROVIDER_NAME", "openai-compatible")
    cloud_base_url: str = os.getenv("KS_CLOUD_BASE_URL", "")
    cloud_api_key: str = os.getenv("KS_CLOUD_API_KEY", "")
    cloud_chat_model: str = os.getenv("KS_CLOUD_CHAT_MODEL", "")
    cloud_embedding_model: str = os.getenv("KS_CLOUD_EMBEDDING_MODEL", "")
    local_provider_name: str = os.getenv("KS_LOCAL_PROVIDER_NAME", "ollama")
    local_base_url: str = os.getenv("KS_LOCAL_BASE_URL", "http://127.0.0.1:11434")
    local_chat_model: str = os.getenv("KS_LOCAL_CHAT_MODEL", "")
    local_embedding_model: str = os.getenv("KS_LOCAL_EMBEDDING_MODEL", "")
    sample_vault_dir: Path = ROOT_DIR / "sample_vault"
    data_dir: Path = ROOT_DIR / "data"
    index_db_path: Path = Path(
        os.getenv("KS_INDEX_DB_PATH", str(ROOT_DIR / "data" / "knowledge_steward.sqlite3"))
    )
    ask_runtime_trace_path: Path = Path(
        os.getenv(
            "KS_ASK_RUNTIME_TRACE_PATH",
            str(ROOT_DIR / "data" / "traces" / "ask_runtime.jsonl"),
        )
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
