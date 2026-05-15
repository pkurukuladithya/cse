# Architecture Overview

This SCADA system demonstrates a full-stack approach to embedded industrial control, bridging low-level hardware interrupts with high-level reactive web interfaces.

## System Diagram

```mermaid
graph TD
    subgraph Hardware Layer
        Motor[N20 Gearmotor]
        Driver[TB6612FNG]
        Enc[Quadrature Encoder]
    end

    subgraph Raspberry Pi 4 (Backend)
        RPiGPIO[RPi.GPIO Interrupts]
        PID[PID Controller Thread]
        Tuner[Auto-Tuner Thread]
        SQLite[(SQLite DB)]
        
        FastAPI[FastAPI Server]
        WS[WebSocket Manager]
    end

    subgraph Web Client (Frontend)
        Zustand[Zustand Store]
        Chart[Recharts Trend]
        UI[React Components]
    end

    %% Hardware <-> Pi
    Driver -->|PWM| Motor
    Motor -->|Rotation| Enc
    Enc -->|Pulses A/B| RPiGPIO
    RPiGPIO -->|Counts| PID
    PID -->|Duty %| Driver
    Tuner -->|Relay %| Driver

    %% Internal Pi
    PID <-->|State Dict| FastAPI
    Tuner <-->|State Dict| FastAPI
    PID -->|Log 4Hz| SQLite
    FastAPI -->|Query| SQLite

    %% Pi <-> Web
    FastAPI <-->|REST API| UI
    WS <-->|JSON 20Hz| Zustand
    Zustand --> Chart
    Zustand --> UI
```

## Data Flow & Timing
1. **Hardware Interrupts**: Encoder pulses are caught by `RPi.GPIO.add_event_detect` on both rising and falling edges for both channels (4x resolution).
2. **PID Loop (50ms)**: A daemon thread wakes exactly every 50ms, calculates RPM, updates metrics (ITAE, overshoot), runs the PID equation, and commands the motor driver.
3. **Database Logging (250ms)**: Every 5th PID tick, the current system state is committed to the SQLite database.
4. **WebSocket Broadcast (50ms)**: The FastAPI async loop pushes the latest `shared_state` dictionary to all connected clients at 20Hz.
5. **Frontend Render**: The `useMotorSocket` hook parses incoming messages and dispatches them to the Zustand store, which triggers a surgical re-render of only the subscribed React components (like the Recharts canvas).
