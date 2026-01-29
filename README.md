# 🦾 GUI-Based Twisted String Actuator / Servo Control System

## Overview
This project implements a **desktop-based GUI application for controlling and monitoring a motor-driven actuator** (servo or Twisted String Actuator) using an **Arduino Nano** over serial communication.

The system is designed for **assistive device prototyping, physiotherapy research, and exoskeletal hand control experiments**, particularly where **independent, precise, finger-level actuation** is required for individuals with impaired hand mobility due to **stroke or neurological injury**.

The application enables **manual, real-time control** of actuator angle, speed, and direction, while providing **live feedback visualization, error analysis, and data logging**.

---

## Key Features
- GUI-based real-time actuator control
- Target angle selection (0°–180°)
- Speed control (fast to slow)
- Clockwise / counter-clockwise direction control
- Robust serial communication with Arduino Nano
- Live feedback monitoring from hardware
- Real-time plotting of commanded vs feedback angle
- Error computation and statistics
- CSV data export for analysis
- Modular and extensible architecture

---

## System Architecture
The system consists of four primary layers:

### 1. GUI Layer (Tkinter)
- User controls for angle, speed, and direction
- START / STOP / RESET controls
- Live status and statistics display

### 2. Serial Communication Layer
- Handles bidirectional communication with Arduino
- Sends control commands
- Receives real-time feedback
- Includes error handling and reconnection logic

### 3. Data Management Layer
- Stores commanded angle, feedback angle, timestamps
- Computes error metrics (average, max, standard deviation)
- Maintains bounded data buffers for efficiency

### 4. Visualization Layer
- Embedded Matplotlib plots
- Live comparison of commanded vs feedback motion
- Real-time error visualization

---

## GUI Controls
- **Angle Slider:** Sets desired actuator angle
- **Speed Slider:** Controls movement speed (1 = fast, 5 = slow)
- **Direction Buttons:** Clockwise / Counter-clockwise rotation
- **START:** Begin actuator movement
- **STOP:** Halt movement immediately
- **Reset:** Return system to default state
- **Save Data:** Export collected data to CSV
- **Clear Data:** Clear stored plots and statistics

---

## Real-Time Visualization
Two plots are displayed during operation:

1. **Commanded vs Feedback Angle**
   - Visual comparison of target and actual actuator motion

2. **Error Plot**
   - Difference between commanded and feedback angle

Plots update continuously and auto-scale as new data arrives.

---

## Data Logging and Analysis
The application logs:
- Timestamp
- Commanded angle
- Feedback angle
- Error (commanded − feedback)

Data can be exported as a **CSV file** for:
- Performance analysis
- Calibration
- Reporting and documentation

---

## Serial Communication Protocol

### Commands Sent to Arduino
