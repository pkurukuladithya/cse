import asyncio
import json
import logging
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from fastapi import BackgroundTasks, FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from auto_tuner import AutoTuner
from config import DATABASE_FILE, DEFAULT_KD, DEFAULT_KI, DEFAULT_KP, DEFAULT_SAMPLE_TIME, DEFAULT_SETPOINT, TELEMETRY_INTERVAL
from logger import (ack_alarm, get_recipes, get_recent_alarms, get_runs, initialize_database, log_alarm, log_run, save_recipe, delete_recipe)
from models import AlarmLevel, AutoTuneParams, RecipeCreate, StatusResponse, WebSocketCommand
from motor_driver import MotorDriver
from pid_controller import PIDController

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="PID SCADA Backend")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIST = BASE_DIR / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


class SCADAServer:
    def __init__(self):
        initialize_database()
        try:
            self.driver = MotorDriver()
            print(f"✓ Motor driver initialized ({'MOCK' if self.driver.use_mock else 'REAL GPIO'})")
        except Exception as exc:
            print(f"✗ Motor driver initialization failed: {exc}")
            raise
        self.pid = PIDController(DEFAULT_KP, DEFAULT_KI, DEFAULT_KD, DEFAULT_SETPOINT, DEFAULT_SAMPLE_TIME)
        self.tuner = AutoTuner(self.read_rpm, self.driver.set_pwm)
        self.clients: Set[WebSocket] = set()
        self.running = False
        self.phase = "idle"
        self.start_time = time.time()
        self.control_task: Optional[asyncio.Task] = None
        self.manual_pwm_values: List[float] = []
        self.last_telemetry: Dict[str, Any] = {}
        self.lock = threading.Lock()

    def read_rpm(self) -> float:
        return self.driver.read_rpm()

    def _phase_label(self, rpm: float) -> str:
        if not self.running:
            return "idle"
        if abs(self.pid.setpoint - rpm) > self.pid.setpoint * 0.2:
            return "ramp"
        if self.phase == "tuning":
            return "tuning"
        return "stable"

    async def control_loop(self) -> None:
        while self.running:
            rpm = self.read_rpm()
            pwm = self.pid.compute(rpm)
            self.driver.set_pwm(pwm)

            self.manual_pwm_values.append(pwm)
            if len(self.manual_pwm_values) > 400:
                self.manual_pwm_values.pop(0)

            data = {
                "rpm": round(rpm, 1),
                "pwm": round(pwm, 1),
                "error": round(self.pid.setpoint - rpm, 1),
                "setpoint": round(self.pid.setpoint, 1),
                "phase": self._phase_label(rpm),
                "ts": time.time(),
            }
            self.last_telemetry = data
            await self.broadcast({"type": "telemetry", "data": data})
            await asyncio.sleep(TELEMETRY_INTERVAL)

    async def broadcast(self, message: Dict[str, Any]) -> None:
        disconnected = []
        payload = json.dumps(message)
        for ws in list(self.clients):
            try:
                await ws.send_text(payload)
            except Exception:
                disconnected.append(ws)
        for ws in disconnected:
            self.clients.discard(ws)

    async def add_client(self, websocket: WebSocket) -> None:
        self.clients.add(websocket)
        await websocket.send_json({"type": "status", "data": self.status_payload()})

    def status_payload(self) -> Dict[str, Any]:
        return {
            "uptime": time.time() - self.start_time,
            "running": self.running,
            "phase": self.phase,
            "telemetry_clients": len(self.clients),
            "pid_params": {
                "kp": self.pid.kp,
                "ki": self.pid.ki,
                "kd": self.pid.kd,
            },
            "setpoint": self.pid.setpoint,
        }

    async def handle_command(self, command: WebSocketCommand) -> None:
        action = command.action
        params = command.params or {}
        if action == "start":
            await self.start()
        elif action == "stop":
            await self.stop()
        elif action == "set_pid":
            await self.set_pid(params)
        elif action == "start_autotune":
            await self.start_autotune(params)
        elif action == "load_recipe":
            await self.load_recipe(params)

    async def start(self) -> None:
        if self.running:
            return
        self.running = True
        self.phase = "ramp"
        self.control_task = asyncio.create_task(self.control_loop())
        log_alarm(AlarmLevel.info, "System START — motor engaging")

    async def stop(self) -> None:
        if not self.running:
            return
        self.running = False
        if self.control_task and not self.control_task.done():
            self.control_task.cancel()
            try:
                await self.control_task
            except asyncio.CancelledError:
                pass
        self.driver.stop()
        self.phase = "idle"
        log_alarm(AlarmLevel.critical, "System STOP — E-STOP engaged")
        if self.last_telemetry:
            pwm_mean = sum(self.manual_pwm_values) / len(self.manual_pwm_values) if self.manual_pwm_values else 0.0
            log_run(
                setpoint=self.pid.setpoint,
                kp=self.pid.kp,
                ki=self.pid.ki,
                kd=self.pid.kd,
                rise_time=self.pid.rise_time,
                overshoot=self.pid.overshoot_pct,
                itae=self.pid.itae,
                settle_time=self.pid.settle_time,
                pwm_mean=pwm_mean,
                source="manual",
            )
            self.manual_pwm_values = []

    async def set_pid(self, params: Dict[str, Any]) -> None:
        kp = float(params.get("kp", self.pid.kp))
        ki = float(params.get("ki", self.pid.ki))
        kd = float(params.get("kd", self.pid.kd))
        setpoint = float(params.get("setpoint", self.pid.setpoint))
        self.pid.update_gains(kp, ki, kd)
        self.pid.setpoint = setpoint
        await self.broadcast({"type": "pid_updated", "data": {"kp": kp, "ki": ki, "kd": kd, "setpoint": setpoint}})

    async def load_recipe(self, params: Dict[str, Any]) -> None:
        recipe_id = int(params.get("id", 0))
        recipes = get_recipes()
        recipe = next((r for r in recipes if r.id == recipe_id), None)
        if recipe is None:
            return
        self.pid.update_gains(recipe.kp, recipe.ki, recipe.kd)
        self.pid.setpoint = self.pid.setpoint
        await self.broadcast({"type": "recipe_loaded", "data": recipe.dict()})

    async def start_autotune(self, params: Dict[str, Any]) -> None:
        if self.phase == "tuning":
            return
        setpoint = float(params.get("setpoint", self.pid.setpoint))
        relay_amp = float(params.get("relay_amp", 20.0))
        self.phase = "tuning"
        await self.broadcast({"type": "autotune_started", "data": {"setpoint": setpoint, "relay_amp": relay_amp}})

        loop = asyncio.get_running_loop()

        def progress_cb(progress: Dict[str, Any]) -> None:
            asyncio.run_coroutine_threadsafe(self.broadcast({"type": "autotune_progress", "data": progress}), loop)

        def run_tuner():
            result = self.tuner.run(setpoint, relay_amp, progress_callback=progress_cb)
            self.pid.update_gains(result["kp"], result["ki"], result["kd"])
            self.pid.setpoint = setpoint
            self.phase = "stable"
            asyncio.run_coroutine_threadsafe(self.broadcast({"type": "autotune_result", "data": result}), loop)
            log_run(
                setpoint=setpoint,
                kp=result["kp"],
                ki=result["ki"],
                kd=result["kd"],
                rise_time=None,
                overshoot=None,
                itae=None,
                settle_time=None,
                pwm_mean=None,
                source="autotune",
            )

        threading.Thread(target=run_tuner, daemon=True).start()

    async def cleanup(self) -> None:
        self.running = False
        self.driver.cleanup()


server = SCADAServer()


@app.get("/api/status", response_model=StatusResponse)
async def get_status() -> StatusResponse:
    payload = server.status_payload()
    return StatusResponse(**payload)


@app.get("/api/runs")
def list_runs(limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
    return [run.dict() for run in get_runs(limit=limit, offset=offset)]


@app.get("/api/recipes")
def list_recipes() -> List[Dict[str, Any]]:
    return [recipe.dict() for recipe in get_recipes()]


@app.post("/api/recipes")
def create_recipe(recipe: RecipeCreate) -> Dict[str, Any]:
    saved = save_recipe(recipe.name, recipe.kp, recipe.ki, recipe.kd, recipe.notes)
    return saved.dict()


@app.delete("/api/recipes/{recipe_id}")
def remove_recipe(recipe_id: int) -> Dict[str, Any]:
    if not delete_recipe(recipe_id):
        raise HTTPException(status_code=404, detail="Recipe not found")
    return {"success": True}


@app.get("/api/alarms")
def list_alarms() -> List[Dict[str, Any]]:
    return [alarm.dict() for alarm in get_recent_alarms()]


@app.post("/api/alarms/{alarm_id}/ack")
def acknowledge_alarm(alarm_id: int) -> Dict[str, Any]:
    if not ack_alarm(alarm_id):
        raise HTTPException(status_code=404, detail="Alarm not found")
    return {"success": True}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    await server.add_client(websocket)
    try:
        while True:
            payload = await websocket.receive_text()
            try:
                command = WebSocketCommand.parse_raw(payload)
                await server.handle_command(command)
            except Exception:
                continue
    except WebSocketDisconnect:
        server.clients.discard(websocket)


@app.on_event("shutdown")
async def shutdown_event() -> None:
    await server.cleanup()


if FRONTEND_DIST.exists():
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str) -> FileResponse:
        index_path = FRONTEND_DIST / "index.html"
        return FileResponse(index_path)
