"""SQLite database module for logging waste detections and generating analytics."""
from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from src.config import DB_PATH, get_class_info


def get_connection(path: Path | str | None = None) -> sqlite3.Connection:
    """Create or return an SQLite connection."""
    target_path = Path(path) if path else DB_PATH
    if target_path != Path(":memory:"):
        target_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(target_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path | str | None = None) -> None:
    """Initialize the SQLite database schema and indices."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS detections (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp      TEXT NOT NULL,
                source         TEXT NOT NULL,
                class_name     TEXT NOT NULL,
                display_name   TEXT NOT NULL,
                confidence     REAL NOT NULL,
                bin_label      TEXT NOT NULL,
                waste_nature   TEXT NOT NULL,
                snapshot_path  TEXT
            )
            """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_detections_timestamp ON detections(timestamp)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_detections_class ON detections(class_name)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_detections_nature ON detections(waste_nature)"
        )
        conn.commit()


def log_detection(
    class_name: str,
    confidence: float,
    source: str = "webcam",
    snapshot_path: str | None = None,
    db_path: Path | str | None = None,
) -> int:
    """Log a waste detection entry into SQLite and return the new row ID."""
    info = get_class_info(class_name)
    now_iso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO detections (
                timestamp, source, class_name, display_name,
                confidence, bin_label, waste_nature, snapshot_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now_iso,
                source,
                class_name,
                info["display_name"],
                round(float(confidence), 4),
                info["bin_label"],
                info["waste_nature"],
                snapshot_path or "",
            ),
        )
        conn.commit()
        return int(cursor.lastrowid)


def get_recent_detections(
    limit: int = 50, db_path: Path | str | None = None
) -> list[dict[str, Any]]:
    """Retrieve the most recent detections."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, timestamp, source, class_name, display_name,
                   confidence, bin_label, waste_nature, snapshot_path
            FROM detections
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_statistics_summary(db_path: Path | str | None = None) -> dict[str, Any]:
    """Calculate key performance indicators and aggregate statistics."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()

        # Total count & average confidence
        cursor.execute("SELECT COUNT(*), AVG(confidence) FROM detections")
        total_row = cursor.fetchone()
        total_count = total_row[0] if total_row else 0
        avg_conf = total_row[1] if total_row and total_row[1] is not None else 0.0

        # Group by class
        cursor.execute(
            """
            SELECT display_name, COUNT(*) as count
            FROM detections
            GROUP BY display_name
            ORDER BY count DESC
            """
        )
        by_class = {row["display_name"]: row["count"] for row in cursor.fetchall()}

        # Group by waste nature
        cursor.execute(
            """
            SELECT waste_nature, COUNT(*) as count
            FROM detections
            GROUP BY waste_nature
            ORDER BY count DESC
            """
        )
        by_nature = {row["waste_nature"]: row["count"] for row in cursor.fetchall()}

        # Group by bin label
        cursor.execute(
            """
            SELECT bin_label, COUNT(*) as count
            FROM detections
            GROUP BY bin_label
            ORDER BY count DESC
            """
        )
        by_bin = {row["bin_label"]: row["count"] for row in cursor.fetchall()}

        return {
            "total_detections": total_count,
            "avg_confidence": round(avg_conf, 4),
            "by_class": by_class,
            "by_nature": by_nature,
            "by_bin": by_bin,
            "most_common_waste": next(iter(by_class.keys()), "Aucun"),
        }


def get_detections_dataframe(db_path: Path | str | None = None) -> pd.DataFrame:
    """Fetch all records as a Pandas DataFrame for Plotly charts."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        df = pd.read_sql_query(
            """
            SELECT id, timestamp, source, display_name, class_name,
                   confidence, bin_label, waste_nature
            FROM detections
            ORDER BY id DESC
            """,
            conn,
        )
        if not df.empty and "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
        return df


def clear_database(db_path: Path | str | None = None) -> None:
    """Delete all records in the detections table (useful for testing or reset)."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM detections")
        conn.commit()

