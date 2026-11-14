"""Unit tests for SQLite database operations and statistics."""
import gc
import tempfile
from pathlib import Path
import pytest
import pandas as pd

from src.database import (
    clear_database,
    get_connection,
    get_detections_dataframe,
    get_recent_detections,
    get_statistics_summary,
    init_db,
    log_detection,
)


@pytest.fixture
def temp_db():
    """Create a temporary database file for isolated testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        temp_path = Path(f.name)
    init_db(temp_path)
    yield temp_path
    gc.collect()
    try:
        if temp_path.exists():
            temp_path.unlink()
    except PermissionError:
        pass


def test_init_db(temp_db):
    """Verify that tables are created properly."""
    with get_connection(temp_db) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='detections'"
        )
        assert cursor.fetchone() is not None


def test_log_and_get_recent_detections(temp_db):
    """Verify logging a detection and fetching recent entries."""
    row_id = log_detection(
        class_name="plastic",
        confidence=0.92,
        source="test",
        db_path=temp_db,
    )
    assert row_id == 1

    recent = get_recent_detections(limit=10, db_path=temp_db)
    assert len(recent) == 1
    assert recent[0]["class_name"] == "plastic"
    assert recent[0]["display_name"] == "Plastique"
    assert recent[0]["confidence"] == 0.92
    assert "Jaune" in recent[0]["bin_label"]
    assert recent[0]["waste_nature"] == "Recyclable"


def test_statistics_summary(temp_db):
    """Verify analytics aggregations (by class, by nature, by bin)."""
    log_detection("plastic", 0.90, db_path=temp_db)
    log_detection("plastic", 0.85, db_path=temp_db)
    log_detection("glass", 0.95, db_path=temp_db)
    log_detection("medical_waste", 0.80, db_path=temp_db)

    stats = get_statistics_summary(db_path=temp_db)
    assert stats["total_detections"] == 4
    assert stats["by_class"]["Plastique"] == 2
    assert stats["by_class"]["Verre"] == 1
    assert stats["by_nature"]["Dangereux"] == 1
    assert stats["most_common_waste"] == "Plastique"


def test_dataframe_export(temp_db):
    """Verify Pandas DataFrame generation."""
    log_detection("metal", 0.88, db_path=temp_db)
    df = get_detections_dataframe(db_path=temp_db)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1
    assert df.iloc[0]["class_name"] == "metal"


def test_clear_database(temp_db):
    """Verify clearing all detections."""
    log_detection("paper", 0.75, db_path=temp_db)
    clear_database(db_path=temp_db)
    stats = get_statistics_summary(db_path=temp_db)
    assert stats["total_detections"] == 0
