"""
main.py
FastAPI application — WebSocket server + REST API + static file serving.
Run with:  uvicorn main:app --host 0.0.0.0 --port 8000
"""
import asyncio
import time
import os
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

import logger
from motor_driver import get_motor_driver
from pid_controller import PIDController
from auto_tuner import AutoTuner

# ─────────────────────────────────────────────
# Initialise DB, hardware, controller
# ─────────────────────────────────────────────
logger.init_db()
motor = get_motor_driver()

# Shared state — single source of truth for everything
state: dict = {
    "target_rpm":   0.0,
    "actual_rpm":   0.0,
    "smoothed_rpm": 0.0,
    "pwm":          0.0,
    "overshoot":    0.0,
    "sse":          0.0,
    "settling_time": 0.0,
    "Kp":           1.5,
    "Ki":           1.5,
    "Kd":           0.0,
    "running":      False,
    "alarm":        None,
    "autotune": {
        "active":   False,
        "status":   "IDLE",
        "progress": 0,
        "result":   None,
        "log":      []
    }
}

pid  = PIDController(motor, state)
tuner = AutoTuner(motor, state)

# ─────────────────────────────────────────────
# FastAPI app
# ─────────────────────────────────────────────
app = FastAPI(title="Industrial PID SCADA", version="2.0.0")

# ── WebSocket connection manager ─────────────
class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        self.active.remove(ws)

    async def broadcast(self, data: dict):
        dead = []
        for ws in self.active:
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.active.remove(ws)

manager = ConnectionManager()


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            await ws.send_json(state)
            await asyncio.sleep(0.05)   # 50ms push
    except WebSocketDisconnect:
        manager.disconnect(ws)


# ── REST Endpoints ───────────────────────────
class UpdateParams(BaseModel):
    target_rpm: Optional[float] = None
    Kp: Optional[float] = None
    Ki: Optional[float] = None
    Kd: Optional[float] = None
    running: Optional[bool] = None


@app.post("/api/update")
async def update_params(params: UpdateParams):
    if params.target_rpm is not None:
        state["target_rpm"] = float(params.target_rpm)
    if params.Kp is not None:
        state["Kp"] = float(params.Kp)
    if params.Ki is not None:
        state["Ki"] = float(params.Ki)
    if params.Kd is not None:
        state["Kd"] = float(params.Kd)
    if params.running is not None:
        state["running"] = bool(params.running)
    return {"status": "ok"}


@app.get("/api/state")
async def get_state():
    return state


class AutoTuneRequest(BaseModel):
    setpoint_rpm: float = 40.0


@app.post("/api/autotune/start")
async def start_autotune(req: AutoTuneRequest):
    if req.setpoint_rpm <= 5:
        raise HTTPException(400, "Setpoint must be > 5 RPM for auto-tune")
    state["running"] = True
    result = tuner.start(req.setpoint_rpm)
    return result


@app.post("/api/autotune/apply")
async def apply_autotune():
    result = state["autotune"].get("result")
    if not result:
        raise HTTPException(400, "No auto-tune result available")
    state["Kp"] = result["Kp"]
    state["Ki"] = result["Ki"]
    state["Kd"] = result["Kd"]
    return {"status": "applied", "Kp": result["Kp"], "Ki": result["Ki"], "Kd": result["Kd"]}


@app.get("/api/history")
async def get_history(limit: int = 300):
    return logger.get_history(limit)


@app.get("/api/alarms")
async def get_alarms(limit: int = 100):
    return logger.get_alarms(limit)


@app.get("/api/recipes")
async def get_recipes():
    return logger.get_recipes()


class RecipeCreate(BaseModel):
    name: str
    kp: float
    ki: float
    kd: float


@app.post("/api/recipes")
async def save_recipe(recipe: RecipeCreate):
    logger.save_recipe(recipe.name, recipe.kp, recipe.ki, recipe.kd)
    return {"status": "saved"}


@app.delete("/api/recipes/{recipe_id}")
async def delete_recipe(recipe_id: int):
    logger.delete_recipe(recipe_id)
    return {"status": "deleted"}


# ── Serve React Frontend ─────────────────────
FRONTEND_DIST = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")

if os.path.isdir(FRONTEND_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST, "assets")), name="assets")

    @app.get("/")
    async def serve_frontend():
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))

    @app.get("/{full_path:path}")
    async def catch_all(full_path: str):
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))
else:
    @app.get("/")
    async def dev_notice():
        return {
            "message": "Backend running. Build the React frontend with 'npm run build' first.",
            "ws": "ws://localhost:8000/ws",
            "api": "/docs"
        }
