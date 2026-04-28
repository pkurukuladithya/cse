# ⚙️ IE3034 Industrial Motor PID Controller

A complete, hardware-in-the-loop Control Systems Engineering project built on a Raspberry Pi 3B+. This system characterizes, tunes, and controls a brushed DC motor using a custom digital PID controller written in Python, featuring anti-windup protection and real-time CPU jitter analysis.

## 🎯 Project Scope & Modules
This repository contains the software implementation for five core control system modules:
1. **System Modelling (Open-Loop):** High-speed data logging to extract the DC Gain ($K$) and Time Constant ($\tau$) of the motor's first-order transfer function.
2. **Closed-Loop Control:** A custom digital PID control loop utilizing hardware-interrupt encoder counting.
3. **Gain Tuning:** Systematic heuristic tuning to achieve minimum settling time and <2% steady-state error.
4. **Disturbance Rejection:** Robustness testing against physical shaft loads and voltage drops.
5. **Performance Analysis:** Real-time calculation of OS-level scheduling jitter and evaluation of encoder quantization noise.

## 🔬 Hardware Architecture
* **Microcontroller:** Raspberry Pi 3B+ (Running Raspberry Pi OS 'Bookworm')
* **Motor Driver:** L298N H-Bridge
* **Actuator:** N20 Brushed DC Motor (with magnetic Hall-effect encoder)
* **Power Supply:** 6V DC Bench Supply

---

## 🛠️ Complete Installation Guide

Because this project utilizes hardware interrupts for precise, microsecond-level encoder counting, it relies on the C-based `pigpio` daemon. Furthermore, to comply with modern Raspberry Pi OS strict package management (PEP 668), all Python libraries must be installed inside an isolated Virtual Environment.

### Step 1: Install OS-Level Dependencies
Open your Raspberry Pi terminal and ensure your system is up to date. Then, install the `pigpio` library and the Python virtual environment package:
```bash
sudo apt update
sudo apt upgrade -y
sudo apt install pigpio python3-venv -y