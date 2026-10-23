import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "routewise.db"


def init_db():
    with sqlite3.connect(DB_PATH, timeout=5) as connection:
        connection.execute("PRAGMA journal_mode=WAL")

        connection.execute("""
            CREATE TABLE IF NOT EXISTS requests (
                request_id TEXT PRIMARY KEY,
                timestamp_utc TEXT NOT NULL,
                status_code INTEGER NOT NULL,
                latency_ms REAL NOT NULL,
                metadata_json TEXT NOT NULL
            )
        """)


def save_request(
    request_id,
    timestamp_utc,
    status_code,
    latency_ms,
    metadata,
):
    allowed_fields = {
        "requested_model",
        "task",
        "reason",
        "attempts",
        "backend",
        "fallback_used",
        "sensitive",
        "allow_paid",    
        "input_tokens",
        "output_tokens",
    }

    safe_metadata = {
        key: value
        for key, value in metadata.items()
        if key in allowed_fields
    }

    with sqlite3.connect(DB_PATH, timeout=5) as connection:
        connection.execute("""
            INSERT INTO requests (
                request_id,
                timestamp_utc,
                status_code,
                latency_ms,
                metadata_json
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            request_id,
            timestamp_utc,
            status_code,
            latency_ms,
            json.dumps(safe_metadata),
        ))


init_db()
