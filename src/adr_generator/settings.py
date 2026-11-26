import os
from collections.abc import Mapping
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    llm_model: str
    embed_model: str
    max_pages: int
    repo_url: str

    @property
    def db_path(self) -> Path:
        return self.data_dir / "github_data.db"

    @property
    def chroma_path(self) -> Path:
        return self.data_dir / "chroma_store"

    @property
    def output_dir(self) -> Path:
        return self.data_dir / "adr_output"


def _positive_int(env: Mapping[str, str], name: str, default: int) -> int:
    raw = env.get(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError:
        raise ValueError(f"{name} must be a whole number, got {raw!r}") from None
    if value < 1:
        raise ValueError(f"{name} must be at least 1, got {value}")
    return value


def load_settings(env: Mapping[str, str] | None = None) -> Settings:
    if env is None:
        env = os.environ
    return Settings(
        data_dir=Path(env.get("ADR_DATA_DIR", "data")),
        llm_model=env.get("ADR_LLM_MODEL", "mistral"),
        embed_model=env.get("ADR_EMBED_MODEL", "nomic-embed-text"),
        max_pages=_positive_int(env, "ADR_MAX_PAGES", 3),
        repo_url=env.get("ADR_REPO_URL", env.get("REPO_URL", "")),
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    load_dotenv(override=False)  # real environment variables win over .env
    return load_settings()