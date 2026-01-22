# Pi Face Presence — Setup Guide

This guide walks you through a clean, reproducible setup of the Pi Face Presence system on a Raspberry Pi 5 using Raspberry Pi OS (64‑bit). It covers camera verification, system packages, Python environment, and running the presence agent.

---

## 1) Hardware & OS

**Required**
- Raspberry Pi 5 (8GB RAM recommended)
- Raspberry Pi Camera Module (CSI ribbon)
- Power supply
- Network (Wi‑Fi or Ethernet)

**OS**
- Raspberry Pi OS 64‑bit (Trixie/Bookworm‑based) with libcamera stack

---

## 2) Verify the Camera (libcamera)

Install camera tools and confirm a live preview:

```bash
sudo apt update
sudo apt install -y rpicam-apps
rpicam-hello
```

You should see a live camera window for a few seconds. If this works, the camera and drivers are correct.

---

## 3) Install System Dependencies

These packages provide OpenCV, the Pi camera Python bindings, build tools, and MQTT (for later integration).

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

Enable the MQTT broker (optional now, required later):

```bash
sudo systemctl enable mosquitto
sudo systemctl start mosquitto
```

---

## 4) Create Project Folder

```bash
mkdir -p ~/pi-face-presence
cd ~/pi-face-presence
```

---

## 5) Create Python Virtual Environment

The Pi camera bindings are provided by the system. Create a venv that can see system packages:

```bash
python3 -m venv --system-site-packages venv
source venv/bin/activate
pip install --upgrade pip setuptools
```

You should see `(venv)` at the start of your prompt.

---

## 6) Install Python Libraries

```bash
pip install numpy opencv-python dlib face-recognition face-recognition-models paho-mqtt langchain langgraph picamera2
```

---

## 7) Create Folder Structure

```bash
mkdir -p faces/Camille faces/Shelby src
```

Add 5–15 clear photos per person:

```text
faces/
├── Camille/
│   ├── 1.jpg
│   ├── 2.jpg
│   └── ...
├── Shelby/
│   ├── 1.jpg
│   ├── 2.jpg
│   └── ...
└── src/
```

Folder names become the identity labels (future Alexa voice output).

---

## 8) Add the Presence Agent

Create the file:

```bash
nano src/presence_agent.py
```

Paste the contents of `presence_agent.py` from the repository, save, and exit.

---

## 9) Run the Agent

```bash
cd ~/pi-face-presence
source venv/bin/activate
python src/presence_agent.py
```

You should see:

```text
[BOOT] Starting Pi Face Presence Agent
[LOAD] Camille: X images
[LOAD] Shelby: Y images
[OK] Loaded Z face encodings
[RUN] Camera online. Press Ctrl+C to stop.
[PRESENCE] Camille
```

Stop with **Ctrl+C**.

---

## 10) Optional Preview Window

If your desktop session supports GUI windows:

```bash
python src/presence_agent.py --show-preview
```

Press **ESC** to close the window.

---

## Troubleshooting

- **Camera works in `rpicam-hello` but not in Python**
  - Ensure `python3-picamera2` is installed
  - Ensure the venv was created with `--system-site-packages`

- **No faces recognized**
  - Check lighting and image quality
  - Ensure images contain a clear, frontal face

- **Slow performance**
  - Reduce resolution in the agent
  - Use `hog` model (default) instead of `cnn`

---

## Next Steps

After setup is complete, the system is ready for:

- Identity enrollment automation
- MQTT presence publishing
- Alexa / Home Assistant integration
- Sound playback and TTS
- Multi‑node smart home and robotics expansion

