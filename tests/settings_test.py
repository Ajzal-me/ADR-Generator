from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from adr_generator.settings import load_settings


def test_defaults():
    s = load_settings({})
    assert s.data_dir == Path("data")
    assert s.llm_model == "mistral"
    assert s.embed_model == "nomic-embed-text"
    assert s.max_pages == 3


def test_env_overrides(tmp_path):
    s = load_settings(
        {
            "ADR_DATA_DIR": str(tmp_path),
            "ADR_LLM_MODEL": "llama3",
            "ADR_EMBED_MODEL": "embed-test",
            "ADR_MAX_PAGES": "5",
            "ADR_REPO_URL": "https://github.com/pallets/flask",
        }
    )
    assert s.data_dir == tmp_path
    assert s.llm_model == "llama3"
    assert s.embed_model == "embed-test"
    assert s.max_pages == 5
    assert s.repo_url == "https://github.com/pallets/flask"


def test_legacy_repo_url_fallback():
    s = load_settings({"REPO_URL": "https://github.com/pallets/flask"})
    assert s.repo_url == "https://github.com/pallets/flask"


def test_derived_paths(tmp_path):
    s = load_settings({"ADR_DATA_DIR": str(tmp_path)})
    assert s.db_path == tmp_path / "github_data.db"
    assert s.chroma_path == tmp_path / "chroma_store"
    assert s.output_dir == tmp_path / "adr_output"


@pytest.mark.parametrize("bad", ["abc", "0", "-2", ""])
def test_bad_max_pages(bad):
    with pytest.raises(ValueError):
        load_settings({"ADR_MAX_PAGES": bad})


def test_settings_are_read_only():
    s = load_settings({})
    with pytest.raises(FrozenInstanceError):
        s.max_pages = 10  # type: ignore[misc]