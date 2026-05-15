import sqlite3
import time
from pathlib import Path
from typing import List, Optional

from config import DATABASE_FILE
from models import AlarmLevel, AlarmRecord, RecipeRecord, RunRecord

DB_PATH = Path(__file__).resolve().parent / DATABASE_FILE


def initialize_database() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS runs (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              ts REAL NOT NULL,
              setpoint REAL,
              kp REAL,
              ki REAL,
              kd REAL,
              rise_time REAL,
              overshoot REAL,
              itae REAL,
              settle_time REAL,
              pwm_mean REAL,
              source TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS alarms (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              ts REAL NOT NULL,
              level TEXT,
              message TEXT,
              cleared INTEGER DEFAULT 0
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS recipes (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              name TEXT UNIQUE NOT NULL,
              kp REAL,
              ki REAL,
              kd REAL,
              notes TEXT,
              created REAL
            )
            """
        )
        conn.commit()


def log_run(setpoint: float, kp: float, ki: float, kd: float, rise_time: Optional[float], overshoot: Optional[float], itae: Optional[float], settle_time: Optional[float], pwm_mean: Optional[float], source: str) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO runs (ts, setpoint, kp, ki, kd, rise_time, overshoot, itae, settle_time, pwm_mean, source) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (time.time(), setpoint, kp, ki, kd, rise_time, overshoot, itae, settle_time, pwm_mean, source),
        )
        conn.commit()


def log_alarm(level: AlarmLevel, message: str) -> int:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
            "INSERT INTO alarms (ts, level, message) VALUES (?, ?, ?)",
            (time.time(), level.value, message),
        )
        conn.commit()
        return cursor.lastrowid


def ack_alarm(alarm_id: int) -> bool:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute("UPDATE alarms SET cleared = 1 WHERE id = ?", (alarm_id,))
        conn.commit()
        return cursor.rowcount > 0


def get_recent_alarms(limit: int = 50) -> List[AlarmRecord]:
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute("SELECT id, ts, level, message, cleared FROM alarms ORDER BY cleared ASC, ts DESC LIMIT ?", (limit,)).fetchall()
    return [AlarmRecord(id=r[0], ts=r[1], level=r[2], message=r[3], cleared=r[4]) for r in rows]


def get_runs(limit: int = 50, offset: int = 0) -> List[RunRecord]:
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            "SELECT id, ts, setpoint, kp, ki, kd, rise_time, overshoot, itae, settle_time, pwm_mean, source FROM runs ORDER BY ts DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
    return [RunRecord(id=r[0], ts=r[1], setpoint=r[2], kp=r[3], ki=r[4], kd=r[5], rise_time=r[6], overshoot=r[7], itae=r[8], settle_time=r[9], pwm_mean=r[10], source=r[11]) for r in rows]


def get_recipes() -> List[RecipeRecord]:
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute("SELECT id, name, kp, ki, kd, notes, created FROM recipes ORDER BY created DESC").fetchall()
    return [RecipeRecord(id=r[0], name=r[1], kp=r[2], ki=r[3], kd=r[4], notes=r[5], created=r[6]) for r in rows]


def save_recipe(name: str, kp: float, ki: float, kd: float, notes: Optional[str] = None) -> RecipeRecord:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
            "INSERT OR REPLACE INTO recipes (name, kp, ki, kd, notes, created) VALUES (?, ?, ?, ?, ?, ?)",
            (name, kp, ki, kd, notes, time.time()),
        )
        conn.commit()
        row_id = cursor.lastrowid
        row = conn.execute("SELECT id, name, kp, ki, kd, notes, created FROM recipes WHERE id = ?", (row_id,)).fetchone()
    return RecipeRecord(id=row[0], name=row[1], kp=row[2], ki=row[3], kd=row[4], notes=row[5], created=row[6])


def delete_recipe(recipe_id: int) -> bool:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute("DELETE FROM recipes WHERE id = ?", (recipe_id,))
        conn.commit()
        return cursor.rowcount > 0
