# Twisted String Actuator GUI for Assistive Hand Rehabilitation

## Overview
This project implements a **GUI-based control system for a motor-driven Twisted String Actuator (TSA)** using an **Arduino Nano**, designed for **physiotherapy and exoskeletal hand rehabilitation**. The system enables controlled finger movement for individuals who have lost partial or complete hand function due to **stroke or neurological impairment**.

The GUI allows **independent, real-time control of each finger**, making it suitable for targeted rehabilitation exercises and assistive hand motion.

---

## System Architecture
The system consists of three main components:
- **GUI Application**: Sends finger-level control commands
- **Microcontroller Unit (Arduino Nano)**: Processes commands and controls actuators
- **Motor-Driven Twisted String Actuators**: Convert motor rotation into linear motion for finger actuation

Commands from the GUI are transmitted to the Arduino, which drives the motor controller to actuate the TSA mechanism accordingly.

---

## Features
- Independent control of each finger
- Real-time motor actuation via GUI commands
- Modular design for scalable finger control
- Designed for assistive and rehabilitation-focused applications
- Low-cost and extensible hardware setup

---

## Hardware Requirements
- Arduino Nano  
- DC motor / geared motor  
- Motor driver module  
- Twisted String Actuator mechanism  
- Power supply  
- Exoskeletal hand or finger actuation setup  

---

## Software Requirements
- Arduino IDE  
- GUI application (custom-built)  
- Serial communication interface  

---

## Applications
- Hand physiotherapy and rehabilitation
- Exoskeletal hand assistance
- Assistive robotics research
- Human–machine interaction studies

---

## Future Improvements
- Sensor-based feedback (force or position sensing)
- Safety limits and calibration routines
- Automated therapy modes
- Closed-loop control algorithms

---

## Disclaimer
This project is intended for **research and educational purposes only**. It is not a certified medical device and should not be used for clinical treatment without proper validation and supervision.

---

## License
This project is open-source and available under the MIT License.
