# Pi Face Presence — Alexa Integration Architecture

This document defines the high‑level architecture for integrating the Pi Face Presence system with Amazon Alexa. It focuses on component roles, data flow, and event logic (not step‑by‑step setup). The goal is to provide a clean, future‑proof blueprint before implementation.

---

## 1. Design Goals

- **Local First**: Face recognition and presence detection run entirely on the Raspberry Pi (no cloud vision).
- **Event Driven**: Alexa reacts to presence *events* (arrivals, departures, identity changes).
- **Loose Coupling**: The presence system and Alexa are connected via a message bus (MQTT), not hard‑wired calls.
- **Extensible**: The same events can trigger sound playback, Home Assistant automations, or robot behaviors.

---

## 2. Core Components

### 2.1 Presence Agent (Raspberry Pi)

`presence_agent.py` is the perception node.

Responsibilities:
- Capture camera frames (Picamera2 / libcamera)
- Detect and recognize faces (OpenCV + dlib)
- Maintain a simple presence state (e.g., Camille present / Shelby present)
- Emit events when state changes

Outputs: Presence events (identity + state + timestamp)

---

### 2.2 Message Bus (MQTT)

MQTT acts as the central nervous system of the smart home.

Responsibilities:
- Receive presence events from the Pi
- Distribute them to all subscribers (Alexa bridge, sound engine, robots, dashboards)
- Decouple producers (vision) from consumers (voice, automation)

This avoids tight coupling and allows multiple devices to react to the same event.

---

### 2.3 Alexa Bridge Service

A lightweight service that translates MQTT presence events into Alexa‑understandable actions.

Two possible implementations:

**Option A: Home Assistant Bridge (Recommended)**
- MQTT → Home Assistant sensors
- Alexa reads Home Assistant entities
- Alexa routines trigger speech and automations

**Option B: Custom Alexa Skill**
- Skill queries a local API that mirrors MQTT state
- Alexa speaks results via TTS

---

### 2.4 Sound / TTS Engine (Local)

A local audio service on the Pi that can:
- Play notification sounds
- Speak names via text‑to‑speech
- Act as an Echo‑Show‑style voice feedback system

This engine will subscribe to the same presence events and respond immediately.

---

## 3. Event Flow

```
[Camera]
   ↓
[Presence Agent]
   ↓  (presence event)
[MQTT Broker]
   ↓            ↓            ↓
[Alexa Bridge] [Sound Engine] [Robots / Automations]
   ↓
[Alexa Voice Output]
```

---

## 4. Presence Event Model

Each presence change is represented as an event with:

- `person`: "Camille" | "Shelby"
- `state`: "arrived" | "departed" | "present" | "absent"
- `location`: "living_room" (future multi‑room support)
- `timestamp`: ISO‑8601 time

Example logical event:

```
Camille → arrived → 2026‑01‑21T18:42:00
```

---

## 5. Alexa Interaction Patterns

### 5.1 Announcements (Push)

Triggered automatically by events:

- "Camille just arrived."
- "Shelby has left the room."

### 5.2 Queries (Pull)

User asks Alexa:

- "Who is home?"
- "Is Camille here?"

Alexa resolves this by reading the latest presence state from the bridge.

---

## 6. Privacy & Security Model

- No images are sent to the cloud
- Only symbolic identity + presence states are published
- MQTT can be restricted to the local network
- Alexa receives only high‑level events, not raw video

---

## 7. Future Expansion

- Multi‑room presence nodes (one Pi per room)
- Wearable / phone presence fusion
- Robot navigation triggers (follow Camille, avoid when Shelby asleep)
- Contextual voice responses ("Welcome home, Camille")

---

This architecture treats Alexa as a *consumer* of presence intelligence, not the owner of it. The Raspberry Pi remains the perception authority, and voice is simply one of many output channels.

