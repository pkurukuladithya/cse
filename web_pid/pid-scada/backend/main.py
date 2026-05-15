"""
main.py
FastAPI application — WebSocket server + REST API + static file serving.

Run on Pi:
  uvicorn main:app --host 0.0.0.0 --port 5000 --workers 1

Dev (laptop):
  uvicorn main:app --host 0.0.0.0 --port 8000 --reload
"""
import asyncio
import time
import os
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

import logger
from motor_driver import get_motor_driver, HARDWARE_AVAILABLE
from pid_controller import PIDController
from auto_tuner import AutoTuner
from models import (
    PIDParamsMsg, AutoTuneRequest, RecipeCreate,
    StatusResponse,
)
from config import (
    DEFAULT_KP, DEFAULT_KI, DEFAULT_KD, DEFAULT_SP,
    WS_TELEMETRY_INTERVAL,
)

# ─────────────────────────────────────────────────────────
# Initialise
# ─────────────────────────────────────────────────────────
logger.init_db()
motor = get_motor_driver()

_start_time = time.time()

# Shared state — single source of truth
state: dict = {
    # Control
    "running":       False,
    "setpoint":      DEFAULT_SP,
    "kp":            DEFAULT_KP,
    "ki":            DEFAULT_KI,
    "kd":            DEFAULT_KD,
    "run_source":    "manual",

    # Telemetry
    "actual_rpm":    0.0,
    "smoothed_rpm":  0.0,
    "pwm":           0.0,
    "error":         0.0,
    "phase":         "idle",

    # KPIs
    "rise_time":     None,
    "overshoot":     0.0,
    "settle_time":   None,
    "itae":          0.0,
    "pwm_mean":      0.0,

    # Alarms
    "alarm":         None,

    # Auto-tune sub-dict (managed by AutoTuner)
    "autotune": {
        "active": False, "status": "idle",
        "progress": 0, "elapsed": 0.0, "total": 60.0,
        "peaks_found": 0, "result": None, "log": [],
    },
}

pid   = PIDController(motor, state)
tuner = AutoTuner(motor, state)

# ─────────────────────────────────────────────────────────
# FastAPI App
# ─────────────────────────────────────────────────────────
app = FastAPI(title="Industrial PID SCADA", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────────────────
# WebSocket Connection Manager
# ─────────────────────────────────────────────────────────
class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self.active:
            self.active.remove(ws)

    async def broadcast(self, data: dict):
        dead = []
        for ws in self.active:
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)

    @property
    def count(self):
        return len(self.active)


manager = ConnectionManager()

# Give tuner a reference to broadcast + event loop
tuner.broadcast_fn = manager.broadcast


@app.on_event("startup")
async def startup():
    tuner.set_event_loop(asyncio.get_event_loop())
    asyncio.create_task(_telemetry_loop())


# ─────────────────────────────────────────────────────────
# Background telemetry broadcast (20Hz)
# ─────────────────────────────────────────────────────────
async def _telemetry_loop():
    while True:
        if manager.count > 0:
            msg = {
                "type": "telemetry",
                "data": {
                    "rpm":        round(state["smoothed_rpm"], 2),
                    "pwm":        round(state["pwm"], 2),
                    "error":      round(state["error"], 2),
                    "setpoint":   state["setpoint"],
                    "phase":      state["phase"],
                    "running":    state["running"],
                    "kp":         state["kp"],
                    "ki":         state["ki"],
                    "kd":         state["kd"],
                    "rise_time":  state.get("rise_time"),
                    "overshoot":  state.get("overshoot"),
                    "settle_time": state.get("settle_time"),
                    "itae":       state.get("itae"),
                    "pwm_mean":   state.get("pwm_mean"),
                    "ts":         time.time(),
                    "autotune":   state["autotune"],
                }
            }
            await manager.broadcast(msg)

            # Forward any pending alarm
            if state.get("alarm"):
                alarm_data = state["alarm"]
                await manager.broadcast({
                    "type": "alarm",
                    "data": {
                        "level":   alarm_data.get("level", "critical"),
                        "message": alarm_data.get("message", "Unknown alarm"),
                        "ts":      time.time(),
                    }
                })
                state["alarm"] = None   # consume it

        await asyncio.sleep(WS_TELEMETRY_INTERVAL)


# ─────────────────────────────────────────────────────────
# WebSocket Endpoint — bidirectional
# ─────────────────────────────────────────────────────────
@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            raw = await ws.receive_json()
            action = raw.get("action")
            params = raw.get("params", {})

            if action == "start":
                state["running"]    = True
                state["run_source"] = "manual"

            elif action == "stop":
                state["running"] = False
                motor.stop()

            elif action == "set_pid":
                if "kp" in params:       state["kp"]       = float(params["kp"])
                if "ki" in params:       state["ki"]       = float(params["ki"])
                if "kd" in params:       state["kd"]       = float(params["kd"])
                if "setpoint" in params: state["setpoint"] = float(params["setpoint"])

            elif action == "start_autotune":
                sp  = float(params.get("setpoint",  60.0))
                amp = float(params.get("relay_amp", 20.0))
                tuner.start(sp, amp)

            elif action == "load_recipe":
                rid    = int(params.get("id", 0))
                recipe = logger.get_recipe_by_id(rid)
                if recipe:
                    state["kp"]       = recipe["kp"]
                    state["ki"]       = recipe["ki"]
                    state["kd"]       = recipe["kd"]
                    state["run_source"] = "recipe"

            else:
                pass  # unknown action — ignore

    except WebSocketDisconnect:
        manager.disconnect(ws)
    except Exception as e:
        print(f"WS error: {e}")
        manager.disconnect(ws)


# ─────────────────────────────────────────────────────────
# REST Endpoints
# ─────────────────────────────────────────────────────────

@app.get("/api/status")
async def get_status():
    return {
        "uptime":            round(time.time() - _start_time, 1),
        "connected_clients": manager.count,
        "running":           state["running"],
        "mock_mode":         not HARDWARE_AVAILABLE,
        "version":           "3.0.0",
    }


@app.get("/api/runs")
async def get_runs(limit: int = 100, offset: int = 0):
    return logger.get_runs(limit=limit, offset=offset)


@app.get("/api/recipes")
async def get_recipes():
    return logger.get_recipes()


@app.post("/api/recipes", status_code=201)
async def save_recipe(recipe: RecipeCreate):
    logger.save_recipe(recipe.name, recipe.kp, recipe.ki, recipe.kd, recipe.notes or "")
    return {"status": "saved"}


@app.delete("/api/recipes/{recipe_id}")
async def delete_recipe(recipe_id: int):
    logger.delete_recipe(recipe_id)
    return {"status": "deleted"}


@app.get("/api/alarms")
async def get_alarms(limit: int = 50):
    return logger.get_alarms(limit=limit)


@app.post("/api/alarms/{alarm_id}/ack")
async def ack_alarm(alarm_id: int):
    logger.ack_alarm(alarm_id)
    return {"status": "acknowledged"}


# ─────────────────────────────────────────────────────────
# Serve React Frontend (built dist/)
# ─────────────────────────────────────────────────────────
FRONTEND_DIST = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
)

if os.path.isdir(FRONTEND_DIST):
    app.mount(
        "/assets",
        StaticFiles(directory=os.path.join(FRONTEND_DIST, "assets")),
        name="assets"
    )

    @app.get("/")
    async def serve_root():
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))

    @app.get("/{full_path:path}")
    async def catch_all(full_path: str):
        f = os.path.join(FRONTEND_DIST, full_path)
        if os.path.isfile(f):
            return FileResponse(f)
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))

else:
    @app.get("/")
    async def dev_notice():
        return {
            "message": "Backend running. Build the React frontend first: cd frontend && npm run build",
            "ws":      "ws://localhost:8000/ws",
            "docs":    "/docs",
        }
