import sqlite3

from adr_generator import database
from adr_generator.agents import writer
from adr_generator.settings import load_settings


def test_database_uses_configured_data_directory(tmp_path, monkeypatch):
    settings = load_settings({"ADR_DATA_DIR": str(tmp_path / "store")})
    monkeypatch.setattr(database, "get_settings", lambda: settings)

    connection = database.get_connection()

    assert isinstance(connection, sqlite3.Connection)
    assert settings.db_path.exists()
    connection.close()


def test_writer_uses_configured_output_directory(tmp_path, monkeypatch):
    settings = load_settings({"ADR_DATA_DIR": str(tmp_path / "store")})
    monkeypatch.setattr(writer, "get_settings", lambda: settings)

    result = writer.writer(
        {
            "draft_adrs": ["# ADR: Example Decision\n\n## Decision\nUse a test."],
        }
    )

    assert result["final_adrs"] == [str(settings.output_dir / "001-example-decision.md")]
    assert (settings.output_dir / "001-example-decision.md").exists()
