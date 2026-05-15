"""
logger.py
SQLite database manager for run history, alarms, and PID recipes.
"""
import sqlite3
import time
import os
from typing import List, Dict, Any

DB_PATH = os.path.join(os.path.dirname(__file__), "database.db")


def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create all tables if they don't exist."""
    conn = _get_conn()
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS runs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   REAL NOT NULL,
            target_rpm  REAL NOT NULL,
            actual_rpm  REAL NOT NULL,
            smoothed_rpm REAL NOT NULL,
            pwm         REAL NOT NULL,
            kp          REAL NOT NULL,
            ki          REAL NOT NULL,
            kd          REAL NOT NULL
        );

        CREATE TABLE IF NOT EXISTS alarms (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   REAL NOT NULL,
            level       TEXT NOT NULL,
            message     TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS recipes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT UNIQUE NOT NULL,
            kp          REAL NOT NULL,
            ki          REAL NOT NULL,
            kd          REAL NOT NULL,
            created_at  REAL NOT NULL
        );
    """)
    conn.commit()
    conn.close()
    print(f"✅ Database initialised at {DB_PATH}")


def log_run(target_rpm, actual_rpm, smoothed_rpm, pwm, kp, ki, kd):
    conn = _get_conn()
    conn.execute(
        "INSERT INTO runs (timestamp, target_rpm, actual_rpm, smoothed_rpm, pwm, kp, ki, kd) "
        "VALUES (?,?,?,?,?,?,?,?)",
        (time.time(), target_rpm, actual_rpm, smoothed_rpm, pwm, kp, ki, kd)
    )
    conn.commit()
    conn.close()


def log_alarm(level: str, message: str):
    """level: 'CRITICAL' | 'WARNING' | 'INFO'"""
    conn = _get_conn()
    conn.execute(
        "INSERT INTO alarms (timestamp, level, message) VALUES (?,?,?)",
        (time.time(), level, message)
    )
    conn.commit()
    conn.close()


def get_history(limit: int = 500) -> List[Dict[str, Any]]:
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM runs ORDER BY timestamp DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in reversed(rows)]


def get_alarms(limit: int = 100) -> List[Dict[str, Any]]:
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM alarms ORDER BY timestamp DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_recipes() -> List[Dict[str, Any]]:
    conn = _get_conn()
    rows = conn.execute("SELECT * FROM recipes ORDER BY name").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_recipe(name: str, kp: float, ki: float, kd: float):
    conn = _get_conn()
    conn.execute(
        "INSERT INTO recipes (name, kp, ki, kd, created_at) VALUES (?,?,?,?,?) "
        "ON CONFLICT(name) DO UPDATE SET kp=excluded.kp, ki=excluded.ki, kd=excluded.kd",
        (name, kp, ki, kd, time.time())
    )
    conn.commit()
    conn.close()


def delete_recipe(recipe_id: int):
    conn = _get_conn()
    conn.execute("DELETE FROM recipes WHERE id=?", (recipe_id,))
    conn.commit()
    conn.close()


def purge_old_runs(days: int = 30):
    """Remove run data older than N days."""
    cutoff = time.time() - (days * 86400)
    conn = _get_conn()
    conn.execute("DELETE FROM runs WHERE timestamp < ?", (cutoff,))
    conn.commit()
    conn.close()
