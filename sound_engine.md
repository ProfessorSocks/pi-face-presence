# Pi Face Presence — Sound Engine Architecture

*(aka: How the house learns to speak without becoming annoying.)*

This document defines the audio and text‑to‑speech (TTS) architecture for Pi Face Presence. It explains how presence events from MQTT are turned into sounds and spoken responses, both locally on the Raspberry Pi and via Alexa.

Agent ID: `serpi5v2`  
Primary Room: `entry_way`

---

## 1. Design Goals

1. **Local First** – Sounds and speech should work even if the internet is down.
2. **Event Driven** – Audio reacts to MQTT presence events, not raw camera frames.
3. **Personality Aware** – Different people can have different sounds or voices.
4. **Polite by Default** – No constant talking; speak only when something meaningful changes.
5. **Future Robot Compatibility** – The same sound engine can be used for robot feedback later.

---

## 2. Components

### 2.1 Presence Agent (Producer)

Publishes events such as:

```
pp/v1/people/Camille/event
pp/v1/people/Shelby/event
```

Payload example:
```json
{
  "person": "Camille",
  "event": "arrived",
  "room": "entry_way",
  "timestamp": "2026-01-22T18:03:00-08:00",
  "source": "serpi5v2"
}
```

---

### 2.2 MQTT Broker (Bus)

Acts as the house intercom. Every device hears the same announcements, then decides what to do with them.

---

### 2.3 Sound Engine Service (Consumer)

A Python service running on the same Pi (or another Pi) that:

- Subscribes to `pp/v1/people/+/event`
- Chooses a response (sound or TTS)
- Plays audio through speakers

It is deliberately dumb about vision and smart about sound.

---

## 3. Audio Types

### 3.1 Notification Sounds

Short, non‑verbal cues:

- Door chime when someone arrives
- Soft tone when someone leaves
- Error tone when camera is blocked

Stored as WAV files, e.g.:

```
sounds/
├── arrival_camille.wav
├── arrival_shelby.wav
├── generic_arrival.wav
├── departure.wav
```

---

### 3.2 Text‑to‑Speech (TTS)

Used for explicit messages:

- "Welcome home, Camille."
- "Shelby just left the entry way."
- "Unknown person detected." (spoken very carefully, because paranoia is expensive.)

Initial engines:

- `espeak-ng` (offline, fast, robotic)
- `piper` (offline, neural, more natural)
- Cloud TTS later (optional, via Alexa)

---

## 4. Decision Logic

The sound engine applies rules:

### 4.1 Arrival

If event = `arrived` and confidence > threshold:

1. Play person‑specific arrival sound (if exists)
2. Speak: "Welcome home, <Person>."

### 4.2 Departure

If event = `departed`:

1. Play soft exit tone
2. Optionally speak: "Goodbye, <Person>."

### 4.3 Re‑detection Spam Filter

If the same person is detected repeatedly within N seconds:

- Do nothing

Because otherwise the house becomes that one friend who won’t stop saying your name.

---

## 5. Topic Subscriptions

The Sound Engine subscribes to:

```
pp/v1/people/+/event
pp/v1/home/state
```

It ignores state unless it needs to answer queries or synchronize.

---

## 6. Configuration Model

Example `sound_config.yaml`:

```yaml
agent_id: serpi5v2
room: entry_way
confidence_threshold: 0.6
cooldown_seconds: 30
voices:
  Camille: female_1
  Shelby: female_2
sounds:
  Camille: sounds/arrival_camille.wav
  Shelby: sounds/arrival_shelby.wav
  default_arrival: sounds/generic_arrival.wav
```

---

## 7. Alexa Interaction

Two layers of sound output exist:

1. **Local Voice (Pi Speaker)** – immediate, offline, low latency
2. **Alexa Voice** – networked, multi‑room, higher quality TTS

Rules:

- Presence Agent → MQTT → Sound Engine (local)
- Presence Agent → MQTT → Alexa Bridge → Alexa speaks

The same event feeds both, but they can use different wording or personalities.

---

## 8. Personality Layer (Fun but Important)

You can later define styles:

```json
{
  "Camille": {
    "greeting": "Welcome home, Camille. Ready to build something?",
    "arrival_sound": "portal_open.wav"
  },
  "Shelby": {
    "greeting": "Hi Shelby. The house missed you.",
    "arrival_sound": "soft_chime.wav"
  }
}
```

Because if you’re building an intelligent home, it should at least be emotionally supportive.

---

## 9. Failure Modes

- **No audio device** → Log only, no crash.
- **TTS engine missing** → Fallback to simple WAV sounds.
- **MQTT disconnected** → Buffer events, play when reconnected.

---

## 10. Next Step

After this architecture is accepted, implementation will add:

- `sound_engine.py`
- MQTT subscriber loop
- WAV playback (ALSA)
- TTS wrapper
- Integration hooks in `presence_agent.py`

---

In summary: the Sound Engine is the voice and ears of your smart home. The Presence Agent sees, MQTT thinks, and the Sound Engine speaks. Ideally with good manners and a sense of humor.

