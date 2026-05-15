"""
models.py
Pydantic request/response models for all REST endpoints.
"""
from pydantic import BaseModel, Field
from typing import Optional


# ── REST Request Models ───────────────────────────────────

class PIDParamsMsg(BaseModel):
    kp:       Optional[float] = Field(None, ge=0, le=20)
    ki:       Optional[float] = Field(None, ge=0, le=20)
    kd:       Optional[float] = Field(None, ge=0, le=5)
    setpoint: Optional[float] = Field(None, ge=0, le=130)


class AutoTuneRequest(BaseModel):
    setpoint:  float = Field(60.0, ge=10, le=100, description="Target RPM for relay test")
    relay_amp: float = Field(20.0, ge=5,  le=50,  description="Relay amplitude in PWM%")


class RecipeCreate(BaseModel):
    name:  str   = Field(..., min_length=1, max_length=64)
    kp:    float = Field(..., ge=0, le=20)
    ki:    float = Field(..., ge=0, le=20)
    kd:    float = Field(..., ge=0, le=5)
    notes: Optional[str] = ""


class AlarmAck(BaseModel):
    alarm_id: int


# ── REST Response Models ──────────────────────────────────

class StatusResponse(BaseModel):
    uptime:           float
    connected_clients: int
    running:          bool
    mock_mode:        bool
    version:          str = "3.0.0"


class RecipeOut(BaseModel):
    id:      int
    name:    str
    kp:      float
    ki:      float
    kd:      float
    notes:   Optional[str]
    created: float


class RunOut(BaseModel):
    id:         int
    ts:         float
    setpoint:   float
    kp:         float
    ki:         float
    kd:         float
    rise_time:  Optional[float]
    overshoot:  Optional[float]
    itae:       Optional[float]
    settle_time: Optional[float]
    pwm_mean:   Optional[float]
    source:     Optional[str]


class AlarmOut(BaseModel):
    id:      int
    ts:      float
    level:   str
    message: str
    cleared: int
