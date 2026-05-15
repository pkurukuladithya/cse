"""
logger.py
SQLite database manager — run history, alarms, recipes.
All operations use context managers for safety.
"""
import sqlite3
import time
from typing import List, Dict, Any, Optional

from config import DB_PATH


# ─────────────────────────────────────────────────────────
# Schema
# ─────────────────────────────────────────────────────────
SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ts          REAL    NOT NULL,
    setpoint    REAL,
    kp          REAL,
    ki          REAL,
    kd          REAL,
    rise_time   REAL,
    overshoot   REAL,
    itae        REAL,
    settle_time REAL,
    pwm_mean    REAL,
    source      TEXT DEFAULT 'manual'
);

CREATE TABLE IF NOT EXISTS alarms (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    ts      REAL    NOT NULL,
    level   TEXT    NOT NULL,
    message TEXT    NOT NULL,
    cleared INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS recipes (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    name    TEXT UNIQUE NOT NULL,
    kp      REAL,
    ki      REAL,
    kd      REAL,
    notes   TEXT DEFAULT '',
    created REAL
);
"""


def init_db():
    """Create all tables if they don't exist."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript(SCHEMA)
    print(f"✅ Database initialised at {DB_PATH}")


# ─────────────────────────────────────────────────────────
# Runs
# ─────────────────────────────────────────────────────────
def log_run(
    setpoint: float,
    kp: float, ki: float, kd: float,
    rise_time:   Optional[float] = None,
    overshoot:   Optional[float] = None,
    itae:        Optional[float] = None,
    settle_time: Optional[float] = None,
    pwm_mean:    Optional[float] = None,
    source:      str = "manual",
):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """INSERT INTO runs
               (ts, setpoint, kp, ki, kd, rise_time, overshoot, itae, settle_time, pwm_mean, source)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (time.time(), setpoint, kp, ki, kd,
             rise_time, overshoot, itae, settle_time, pwm_mean, source)
        )


def get_runs(limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM runs ORDER BY ts DESC LIMIT ? OFFSET ?",
            (limit, offset)
        ).fetchall()
    return [dict(r) for r in rows]


# ─────────────────────────────────────────────────────────
# Alarms
# ─────────────────────────────────────────────────────────
def log_alarm(level: str, message: str):
    """level: 'info' | 'warn' | 'critical'"""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO alarms (ts, level, message) VALUES (?,?,?)",
            (time.time(), level.lower(), message)
        )


def get_alarms(limit: int = 50) -> List[Dict[str, Any]]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """SELECT * FROM alarms
               ORDER BY cleared ASC, ts DESC
               LIMIT ?""",
            (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


def ack_alarm(alarm_id: int):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "UPDATE alarms SET cleared=1 WHERE id=?",
            (alarm_id,)
        )


# ─────────────────────────────────────────────────────────
# Recipes
# ─────────────────────────────────────────────────────────
def get_recipes() -> List[Dict[str, Any]]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM recipes ORDER BY name"
        ).fetchall()
    return [dict(r) for r in rows]


def save_recipe(name: str, kp: float, ki: float, kd: float, notes: str = ""):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """INSERT INTO recipes (name, kp, ki, kd, notes, created)
               VALUES (?,?,?,?,?,?)
               ON CONFLICT(name) DO UPDATE
               SET kp=excluded.kp, ki=excluded.ki, kd=excluded.kd,
                   notes=excluded.notes""",
            (name, kp, ki, kd, notes, time.time())
        )


def delete_recipe(recipe_id: int):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM recipes WHERE id=?", (recipe_id,))


def get_recipe_by_id(recipe_id: int) -> Optional[Dict[str, Any]]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM recipes WHERE id=?", (recipe_id,)
        ).fetchone()
    return dict(row) if row else None
