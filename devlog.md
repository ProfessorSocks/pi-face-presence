# Pi Face Presence — Development Log

This document records the full engineering process of bringing up the first working version of the Pi Face Presence system on a Raspberry Pi 5, including environment setup, camera stack issues, Python packaging problems, and face recognition integration.

The README contains only the clean, working instructions. This file captures what *actually* happened and what was learned.

---

## 1. Platform

**Hardware**
- Raspberry Pi 5 (8GB RAM)
- Raspberry Pi Camera Module (CSI)

**OS**
- Raspberry Pi OS 64‑bit (Debian Trixie base)
- Raspberry Pi firmware and libcamera stack

**Access Method**
- Raspberry Pi Connect (remote desktop)
- SSH

---

## 2. Initial Goal

Build a local, privacy‑preserving face presence system that:
- Runs entirely on-device
- Recognizes specific people (Camille, Shelby)
- Is future‑proof for Alexa, MQTT, sound playback, and robotics
- Acts as a low‑cost alternative to an Echo Show‑style presence display

---

## 3. Camera Stack Lessons

### libcamera vs V4L2

OpenCV’s `VideoCapture(0)` failed because:
- Raspberry Pi 5 uses the libcamera pipeline
- CSI cameras do not reliably expose a standard `/dev/video0` device

Correct approach:
- Use `rpicam-hello` to verify hardware
- Use `picamera2` as the Python interface

Working verification:
```bash
rpicam-hello
```

Python capture must use:
```python
from picamera2 import Picamera2
```

---

## 4. Python Environment

### PEP 668: Externally Managed Environment

System Python blocked pip installs.
Solution:
- Use a virtual environment
- But allow system camera bindings

Correct venv creation:
```bash
python3 -m venv --system-site-packages venv
source venv/bin/activate
```

This allows `picamera2` and `libcamera` to remain visible inside the venv.

---

## 5. Face Recognition Stack

Libraries used:
- OpenCV
- dlib
- face_recognition
- face_recognition_models

Key issue:
- Python 3.13 deprecated `pkg_resources`
- Installing `setuptools` resolved missing imports

---

## 6. Training Data Structure

Final folder layout:
```
faces/
├── Camille/
│   ├── *.jpg
├── Shelby/
│   ├── *.jpg
src/
└── presence_agent.py
```

Each folder name becomes the identity label (future Alexa TTS friendly).

---

## 7. First Working Agent

Created: `src/presence_agent.py`

Capabilities:
- Loads all images under `faces/<Name>`
- Encodes faces using dlib
- Captures live frames via Picamera2
- Matches against known embeddings
- Prints presence events:
  ```
  [PRESENCE] Camille
  [PRESENCE] Shelby
  [PRESENCE] Unknown
  ```

This script is intentionally structured for later upgrades:
- MQTT publishing
- Alexa speech
- Sound playback
- Robot navigation triggers

---

## 8. Git & Documentation Workflow

- GitHub Desktop not available for Linux
- VS Code Git panel used as GUI
- Repo structured for public replication
- README and RUN_INSTRUCTIONS.md created

---

## 9. Major Engineering Takeaways

1. Raspberry Pi camera development must be built around **libcamera + picamera2**.
2. Python venvs on Pi must expose system packages for camera bindings.
3. Face recognition pipelines must separate:
   - capture
   - detection
   - encoding
   - identity matching
4. Folder naming becomes the future voice identity for Alexa.
5. Architecture must be designed from day one for distributed robotics and smart-home messaging.

---

## 10. Next Phases

Planned upgrades:

1. **Identity enrollment tool** (auto-capture training photos)
2. **MQTT presence publisher**
3. **Alexa TTS integration**
4. **Sound playback system**
5. **Home Assistant bridge**
6. **Robot perception node mode**

---

This dev log represents the foundation of a full local AI perception system suitable for smart homes and autonomous robots, built with privacy-first principles and open hardware.

