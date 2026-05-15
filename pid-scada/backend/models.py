from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class AlarmLevel(str, Enum):
    info = "info"
    warn = "warn"
    critical = "critical"


class RecipeCreate(BaseModel):
    name: str = Field(..., min_length=1)
    kp: float
    ki: float
    kd: float
    notes: Optional[str] = None


class RecipeRecord(BaseModel):
    id: int
    name: str
    kp: float
    ki: float
    kd: float
    notes: Optional[str]
    created: float


class AlarmRecord(BaseModel):
    id: int
    ts: float
    level: AlarmLevel
    message: str
    cleared: int


class RunRecord(BaseModel):
    id: int
    ts: float
    setpoint: float
    kp: float
    ki: float
    kd: float
    rise_time: Optional[float]
    overshoot: Optional[float]
    itae: Optional[float]
    settle_time: Optional[float]
    pwm_mean: Optional[float]
    source: str


class StatusResponse(BaseModel):
    uptime: float
    running: bool
    phase: str
    telemetry_clients: int
    pid_params: dict
    setpoint: float
    version: str = "backend-1.0"


class WebSocketCommand(BaseModel):
    action: str
    params: Optional[dict] = None


class AutoTuneParams(BaseModel):
    setpoint: float
    relay_amp: float


class AcknowledgeResponse(BaseModel):
    success: bool
    message: str
