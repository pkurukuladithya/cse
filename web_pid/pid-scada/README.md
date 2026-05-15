# Industrial PID SCADA System

![SCADA Dashboard Dashboard Placeholder](https://via.placeholder.com/1200x600/0c1420/00c8e8?text=Industrial+SCADA+Dashboard)

A production-quality Industrial SCADA system demonstrating full-stack engineering applied to embedded motor control. This project bridges low-level hardware interrupts on a Raspberry Pi with a high-performance, real-time React dashboard.

## 🚀 Key Features

1. **Closed-Loop PID Control**
   Features a from-scratch industrial PID implementation including:
   - **Anti-windup**: Integral clamping to prevent saturation runaway.
   - **Derivative on Measurement**: Prevents derivative kick during sudden setpoint changes.
   - **Bumpless Transfer**: Seamless parameter updates without output jumps.

2. **Ziegler-Nichols Auto-Tuning**
   Implements a relay feedback method (bang-bang control) to induce sustained motor oscillations. It calculates the Ultimate Gain ($K_u$) and Ultimate Period ($T_u$) on the fly, applying classic Z-N formulas to automatically derive $K_p, K_i, K_d$ parameters.

3. **Real-Time Architecture**
   - **Backend**: FastAPI running a 50ms background control loop alongside an asynchronous WebSocket manager.
   - **Frontend**: React 18 + Zustand global state. Receives 20Hz telemetry via WebSockets and renders a rolling 600-point time-series chart using Recharts without dropping frames.

4. **Data Persistence**
   SQLite handles logging of run history, alarm events, and saved PID recipes, executing via context managers to ensure thread safety.

## ⚙️ Hardware Setup

```
Microcontroller : Raspberry Pi 4 Model B
Motor           : N20 DC gearmotor with quadrature encoder (PPR: 7, 30:1 ratio)
Driver          : TB6612FNG dual H-bridge
Power Supply    : 5.28V regulated external
```

**Wiring / GPIO Pinout (BCM):**
- `GPIO 12` : PWMA (Hardware PWM at 1kHz)
- `GPIO 23` : AIN1 (Direction)
- `GPIO 24` : AIN2 (Direction)
- `GPIO 25` : STBY (Active HIGH enable)
- `GPIO 17` : ENC_A (Interrupt on both edges)
- `GPIO 27` : ENC_B (Interrupt on both edges)

## 💻 Development & Deployment

### 1. Build the Frontend
```bash
cd frontend
npm install
npm run build
```

### 2. Run the Backend (Raspberry Pi)
The backend automatically detects if it's running on a Raspberry Pi. If not, it falls back to a **Mock Driver** simulating a first-order system with Gaussian noise, allowing for seamless development on any OS.

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 5000 --workers 1
```

Access the dashboard at `http://<raspberry-pi-ip>:5000`

## 🔮 Future Roadmap
- **Machine Learning**: Integration of Bayesian Optimization to find optimal PID gains over time, replacing the heuristic Z-N approach.
- **System Identification**: Automatically generate transfer function models based on step-response data.

---
*Built with React, FastAPI, framer-motion, and RPi.GPIO.*
