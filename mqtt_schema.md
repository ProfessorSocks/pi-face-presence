# Pi Face Presence — MQTT Schema (a.k.a. the Smart‑Home Gossip Protocol)

This document specifies the MQTT topic structure and message payloads for **Pi Face Presence**.

Goal: make the Raspberry Pi presence system (vision) publish clean, privacy‑safe events that **Alexa**, **Home Assistant**, **sound playback**, **robots**, and future devices can subscribe to without needing to know anything about cameras or face embeddings.

> **Tone note:** This is a serious spec wearing a novelty hat. If you see jokes, it’s because humor is a valid coping strategy when debugging distributed systems.

---

## 0) Quick summary

- MQTT broker is the house “town square.”
- The Presence Agent publishes **events** (arrived/left) and **state** (present/absent + mood/context).
- Consumers (Alexa bridge, sound engine, robots) subscribe and react.

---

## 1) Naming philosophy (why the “structured” style feels better)

You said you’re torn between *human readable* and *machine structured*. Here’s the key:

### Human readable
Example:

```
home/presence/Camille
home/room/living_room/presence
```

Pros:
- Easy to read in MQTT Explorer
- Feels natural

Cons:
- Mixing **category** and **identity** in the path makes it harder to scale
- People names in topic paths become awkward if you later add:
  - nicknames
  - devices
  - multiple homes
  - multiple rooms
  - multiple presence nodes
- Harder to add consistent “state vs event” separation

### Machine structured (recommended)
Example:

```
pp/v1/people/Camille/state
pp/v1/people/Camille/event
pp/v1/rooms/living_room/state
pp/v1/system/agent/status
```

Why it “feels better”:
- Topics read like an API: **domain/entity/kind**
- Scales cleanly to more rooms, more Pis, more robots
- Lets you keep payloads consistent
- Easy to wildcard subscribe:
  - `pp/v1/people/+/event`
  - `pp/v1/rooms/+/state`

**Best of both worlds:** we keep names human readable *inside* the structured path (so you still see “Camille” in plain English), but we organize the hierarchy so your future self doesn’t curse your present self.

---

## 2) Topic namespace

We use a project namespace prefix so we don’t collide with other MQTT stuff:

```
pp/        = Pi Face Presence
v1/        = schema version (so we can evolve safely)
```

So everything starts with:

```
pp/v1/
```

---

## 3) Core entities

### 3.1 People
- `Camille`
- `Shelby`

People names are **folder names** under `faces/` (case‑sensitive on Linux).

### 3.2 Rooms
Start simple:
- `living_room`

(You can add rooms later without changing the schema.)

### 3.3 Agent
- the presence node itself (the Pi running `presence_agent.py`)

---

## 4) Event vs State (this matters)

### Event
A short-lived message meaning “something happened.”
Examples:
- Camille arrived
- Shelby left
- Unknown face detected

Events are used for:
- announcements
- sounds
- automation triggers

### State
The current truth “as of now.”
Examples:
- Camille is present
- living_room occupancy = 1
- agent is online

States are used for:
- queries (“who is home?”)
- dashboards
- robots needing stable knowledge

**Rule of thumb:**
- Events are notifications.
- State is the latest fact.

---

## 5) Topics

### 5.1 Agent health

**Agent status (retained):**

```
pp/v1/system/agent/status
```

Payload:
```json
{
  "agent_id": "serpi5v2",
  "state": "online",
  "version": "0.1.0",
  "timestamp": "2026-01-22T17:00:00-08:00"
}
```

**Why retained?** So subscribers coming online later immediately learn the agent is alive.

---

### 5.2 People state (retained)

```
pp/v1/people/<Person>/state
```

Examples:
- `pp/v1/people/Camille/state`
- `pp/v1/people/Shelby/state`

Payload:
```json
{
  "person": "Camille",
  "present": true,
  "room": "living_room",
  "confidence": 0.86,
  "mood": "playful",
  "activity": "building_robots",
  "last_seen": "2026-01-22T17:01:12-08:00",
  "source": "serpi5v2"
}
```

Notes:
- `mood` / `activity` are optional now, but the schema reserves them for future contextual states.
- `confidence` helps decide whether Alexa should speak or stay politely silent.

---

### 5.3 People events (not retained)

```
pp/v1/people/<Person>/event
```

Payload:
```json
{
  "person": "Camille",
  "event": "arrived",
  "room": "living_room",
  "confidence": 0.86,
  "timestamp": "2026-01-22T17:01:12-08:00",
  "source": "serpi5v2"
}
```

Allowed events:
- `arrived`
- `departed`
- `seen` (optional: periodic heartbeat when still present)
- `unknown_seen` (optional: if you later track guests)

**Not retained** because events are meant to be consumed once.

---

### 5.4 Room state (retained)

```
pp/v1/rooms/<Room>/state
```

Example:
- `pp/v1/rooms/living_room/state`

Payload:
```json
{
  "room": "living_room",
  "occupancy": 1,
  "people": ["Camille"],
  "last_update": "2026-01-22T17:01:12-08:00",
  "source": "serpi5v2"
}
```

---

### 5.5 “Who is home?” convenience state (retained)

This is a helper for Alexa queries.

```
pp/v1/home/state
```

Payload:
```json
{
  "home": true,
  "people": ["Camille", "Shelby"],
  "last_update": "2026-01-22T17:05:00-08:00"
}
```

If you want your smart home to have ✨drama✨ you can also add:

```json
{ "vibes": "immaculate" }
```

(Professional note: keep that out of production logs unless your employer is cool.)

---

## 6) Payload standards

### 6.1 Timestamp format
Use ISO‑8601 with timezone:

- `2026-01-22T17:01:12-08:00`

### 6.2 JSON only
All payloads are JSON objects.

### 6.3 Required keys
For most messages:
- `timestamp`
- `source`

Because debugging is hard enough without guessing which Pi spoke.

---

## 7) QoS & Retain policy

### QoS
- **QoS 0** for high-frequency things (frames, rapid updates)
- **QoS 1** for important events (arrived/departed)

Recommended defaults:
- `people/<Person>/event` → QoS 1
- `people/<Person>/state` → QoS 1
- `rooms/<Room>/state` → QoS 1

### Retain
- Retain **state** topics
- Do **not** retain **event** topics

Otherwise new subscribers will replay old arrivals and your house will sound haunted.

---

## 8) Subscriptions (consumer roles)

### Alexa Bridge
- Subscribe: `pp/v1/people/+/event`
- Subscribe: `pp/v1/home/state`

Logic:
- If `event == arrived` → speak greeting
- If asked "who is home" → read `home/state`

### Sound Engine
- Subscribe: `pp/v1/people/+/event`

Logic:
- Play sound on arrival
- Optional: different sound per person

### Robots
- Subscribe: `pp/v1/rooms/+/state`
- Subscribe: `pp/v1/people/+/state`

Logic:
- Navigation rules
- Safety rules
- Context rules

---

## 9) Example end-to-end sequence

1) Camille walks into frame.
2) Presence agent recognizes Camille with confidence 0.86.
3) Agent publishes:
- `pp/v1/people/Camille/event` { arrived }
- `pp/v1/people/Camille/state` { present=true }
- `pp/v1/rooms/living_room/state` { occupancy=1 }
- `pp/v1/home/state` { people=[Camille] }

4) Alexa bridge hears `arrived` and says:
> “Welcome home, Camille.”

5) Sound engine plays a triumphant beep.

6) Robot hears Camille is present and decides not to run vacuum mode (for now).

---

## 10) Versioning

Schema version is in the topic path: `pp/v1/...`

When we make breaking changes:
- introduce `pp/v2/...`
- keep v1 running until consumers migrate

This prevents the classic smart-home failure mode where one script update causes everything to stop working and you start bargaining with the universe.

---

## 11) Next doc

After this schema is approved, implement:
- MQTT publishing in `presence_agent.py`
- and then define the audio pipeline in **SOUND_ENGINE.md**.

