"""Pi Face Presence — sound_engine.py

Local Sound + TTS engine (offline) that reacts to MQTT events.

This is the "voice box" of the system:
- Presence Agent sees (camera)
- MQTT distributes (nervous system)
- Sound Engine speaks (and plays sounds)

Default greeting style:
  "Hi <Person>! You’re home."

Run (in a second terminal):
  source venv/bin/activate
  python src/sound_engine.py

Requires:
- mosquitto running locally
- espeak-ng installed for offline speech

"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import time
from dataclasses import dataclass
from typing import Dict, Optional

import paho.mqtt.client as mqtt


MQTT_BASE = "pp/v1"


@dataclass
class SoundConfig:
    agent_id: str
    room: str
    confidence_threshold: float
    cooldown_seconds: int
    greeting_template: str


def mqtt_topic(*parts: str) -> str:
    return "/".join([MQTT_BASE, *parts])


def speak_espeak(text: str, voice: Optional[str] = None) -> None:
    """Offline TTS via espeak-ng. Non-blocking-ish (spawns process)."""
    cmd = ["espeak-ng", "-s", "165", "-a", "140"]
    if voice:
        cmd += ["-v", voice]
    cmd += [text]

    try:
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        print("[WARN] espeak-ng not found. Install: sudo apt install espeak-ng")
    except Exception as e:
        print(f"[WARN] TTS failed: {e}")


def play_wav(path: str) -> None:
    """Play a WAV file using aplay (ALSA)."""
    if not path:
        return
    if not os.path.exists(path):
        print(f"[WARN] Sound file missing: {path}")
        return

    try:
        subprocess.Popen(["aplay", "-q", path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        print("[WARN] aplay not found. Install: sudo apt install alsa-utils")
    except Exception as e:
        print(f"[WARN] Audio playback failed: {e}")


class Engine:
    def __init__(self, cfg: SoundConfig):
        self.cfg = cfg
        self.last_spoken: Dict[str, float] = {}  # person -> epoch

        # Optional per-person sound map (fill in later):
        self.arrival_sounds: Dict[str, str] = {
            # "Camille": "sounds/arrival_camille.wav",
            # "Shelby": "sounds/arrival_shelby.wav",
        }
        self.default_arrival_sound: str = ""  # e.g., "sounds/generic_arrival.wav"

        # Optional per-person espeak voices (fill in later):
        self.voices: Dict[str, str] = {
            # "Camille": "en-us",
            # "Shelby": "en-us",
        }

    def should_speak(self, person: str) -> bool:
        now = time.time()
        last = self.last_spoken.get(person, 0.0)
        if (now - last) < self.cfg.cooldown_seconds:
            return False
        self.last_spoken[person] = now
        return True

    def on_arrived(self, person: str, confidence: float, room: str, source: str) -> None:
        if room != self.cfg.room:
            return
        if confidence < self.cfg.confidence_threshold:
            print(f"[SKIP] Low confidence for {person}: {confidence:.3f}")
            return
        if not self.should_speak(person):
            return

        # Play sound (if configured)
        wav = self.arrival_sounds.get(person) or self.default_arrival_sound
        if wav:
            print(f"[SOUND] {person} arrival -> {wav}")
            play_wav(wav)

        # Speak greeting
        text = self.cfg.greeting_template.replace("{person}", person).replace("{room}", room)
        print(f"[TTS] {text}")
        speak_espeak(text, voice=self.voices.get(person))

    def on_departed(self, person: str, room: str) -> None:
        # Optional: departure behavior later
        pass


def main() -> int:
    parser = argparse.ArgumentParser(description="Pi Face Presence — Sound Engine (MQTT consumer)")
    parser.add_argument("--mqtt-host", default="localhost")
    parser.add_argument("--mqtt-port", type=int, default=1883)
    parser.add_argument("--agent-id", default="serpi5v2")
    parser.add_argument("--room", default="entry_way")
    parser.add_argument("--confidence-threshold", type=float, default=0.60)
    parser.add_argument("--cooldown-seconds", type=int, default=30)
    parser.add_argument(
        "--greeting",
        default="Hi {person}! You’re home.",
        help="Greeting template (placeholders: {person}, {room})",
    )

    args = parser.parse_args()

    cfg = SoundConfig(
        agent_id=args.agent_id,
        room=args.room,
        confidence_threshold=args.confidence_threshold,
        cooldown_seconds=args.cooldown_seconds,
        greeting_template=args.greeting,
    )

    engine = Engine(cfg)

    def on_connect(client, userdata, flags, reason_code, properties=None):
        print(f"[MQTT] Connected (reason={reason_code}). Subscribing...")
        client.subscribe(mqtt_topic("people", "+", "event"), qos=1)

    def on_message(client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
        except Exception:
            print(f"[WARN] Non-JSON payload on {msg.topic}")
            return

        person = payload.get("person")
        event = payload.get("event")
        room = payload.get("room")
        confidence = float(payload.get("confidence", 0.0))
        source = payload.get("source")

        # Ignore messages not from our agent if you want single-node behavior.
        # For multi-node later, remove this filter.
        if source and source != cfg.agent_id:
            return

        if event == "arrived":
            engine.on_arrived(person, confidence, room, source)
        elif event == "departed":
            engine.on_departed(person, room)

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message

    print("[BOOT] Sound Engine starting.")
    print(f"[CFG] room={cfg.room}, threshold={cfg.confidence_threshold}, cooldown={cfg.cooldown_seconds}s")
    print("[NOTE] Install deps if needed: sudo apt install espeak-ng alsa-utils")

    client.connect(args.mqtt_host, args.mqtt_port, keepalive=60)
    client.loop_forever()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
