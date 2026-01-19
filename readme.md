# Pi Face Presence

**Pi Face Presence** is a privacy-first, local face presence and identity detection system built on a Raspberry Pi. It is designed as a low-cost, extensible alternative to smart displays like the Amazon Echo Show, allowing you to detect *who is home* without relying on cloud vision or expensive hardware.

This project is part of the **ProfessorSocks / Gingerbread** ecosystem and is intended to integrate with Alexa, smart home platforms, and future robotic systems.

---

## Project Goals

- Build a local, on-device face recognition system (no cloud processing)
- Detect when a person is present and identify who they are
- Publish presence information to a smart home message bus (MQTT)
- Integrate with Alexa for voice announcements and queries
- Provide an open, replicable alternative to devices like the Echo Show 8
- Serve as a future perception module for mobile robots

---

## Hardware Used

Tested configuration:

- Raspberry Pi 5 (8GB RAM)
- Raspberry Pi Camera Module (CSI ribbon camera)
- Power supply
- Network connection (Wi‑Fi or Ethernet)

Optional (for future voice features):

- USB microphone
- Small speaker
- HDMI display (for UI / dashboard)

---

## Software Stack

- Raspberry Pi OS 64‑bit (libcamera / rpicam stack)
- Python 3.13
- picamera2 (camera capture)
- OpenCV (image processing)
- dlib + face_recognition (face detection & encoding)
- Mosquitto (MQTT broker)
- LangGraph (future agent logic)
- Python virtual environment with system camera bindings

---

## System Architecture

```
[Pi Camera Module]
        ↓
   [libcamera]
        ↓
   [Picamera2]
        ↓
    [OpenCV]
        ↓
[face_recognition / dlib]
        ↓
 [Identity & Presence State]
        ↓
       [MQTT]
        ↓
 [Alexa / Home Assistant / Robots]
```

All processing runs locally on the Raspberry Pi for privacy and low latency.

---

## What Currently Works

- Raspberry Pi camera verified using `rpicam-hello`
- Python environment configured for Pi 5 camera stack
- picamera2 integrated with OpenCV
- face_recognition library installed and loading correctly
- Live face detection pipeline operational
- Architecture prepared for MQTT publishing and Alexa integration

---

## Planned Features

- Identity enrollment (store known faces)
- Real‑time recognition loop with presence state tracking
- MQTT topic publishing for smart home automation
- Alexa integration ("Who is home?" / "Camille just arrived")
- Home Assistant bridge
- Optional UI (Echo‑Show‑style dashboard)
- Optional mobile robot perception module

---

## Setup Overview

### 1. Verify Camera

```bash
sudo apt install rpicam-apps
rpicam-hello
```

If you see a live preview, the camera stack is working.

---

### 2. Install System Dependencies

```bash
sudo apt update
sudo apt install -y \
  python3-opencv \
  python3-venv \
  python3-pip \
  cmake \
  libopenblas-dev \
  libjpeg-dev \
  libpng-dev \
  libavcodec-dev \
  libavformat-dev \
  libswscale-dev \
  libgtk-3-dev \
  mosquitto \
  mosquitto-clients \
  python3-picamera2
```

Enable MQTT:

```bash
sudo systemctl enable mosquitto
sudo systemctl start mosquitto
```

---

### 3. Create Virtual Environment

```bash
mkdir pi-face-presence
cd pi-face-presence
python3 -m venv --system-site-packages venv
source venv/bin/activate
pip install --upgrade pip setuptools
```

---

### 4. Install Python Dependencies

```bash
pip install numpy opencv-python dlib face-recognition face-recognition-models paho-mqtt langchain langgraph picamera2
```

---

### 5. Test Face Detection

Create `test_face.py`:

```python
from picamera2 import Picamera2
import cv2
import face_recognition
import time

picam = Picamera2()
config = picam.create_preview_configuration(main={"size": (640, 480)})
picam.configure(config)
picam.start()
time.sleep(1.5)

while True:
    frame = picam.capture_array()
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    faces = face_recognition.face_locations(rgb)
    print("Faces detected:", len(faces))

    cv2.imshow("Pi Face Presence", frame)
    if cv2.waitKey(1) & 0xFF == 27:
        break

cv2.destroyAllWindows()
picam.stop()
```

Run:

```bash
python test_face.py
```

Press **ESC** to exit.

---

## Smart Home Integration Plan

### MQTT Topics (Planned)

- `home/presence` → home / away
- `home/people/camille` → present / away
- `home/people/shelby` → present / away

### Alexa Integration (Planned)

Two approaches:

1. Home Assistant bridge (recommended)
2. Custom Alexa Skill querying MQTT presence API

Example voice interactions:

- “Alexa, who is home?”
- “Alexa, is Camille home?”
- “Alexa, announce when someone arrives.”

---

## Future Expansion

- Face embedding database
- Confidence thresholds
- Privacy modes (camera off when home)
- Robot navigation perception
- Multi‑room distributed presence nodes
- Local voice assistant fallback (offline TTS / STT)

---

## Philosophy

This project demonstrates that:

- Smart home AI does not need to live in the cloud
- Face recognition can be done privately and locally
- A low‑cost Raspberry Pi can replace expensive consumer hardware
- The same perception stack can power homes and robots

---

## License

MIT (recommended)

