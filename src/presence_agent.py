"""
Pi Face Presence — presence_agent.py

Future-proof face presence + identity agent for Raspberry Pi.

Today:
- Loads known identities from ./faces/<Name>/*.jpg
- Runs live camera capture using Picamera2 (Pi 5 / libcamera stack)
- Prints recognized names to the terminal

Next upgrades (designed for):
- MQTT publishing
- Alexa / Home Assistant integration
- Sound playback / TTS

Folder layout expected (case-sensitive on Linux):
  ./faces/Camille/
  ./faces/Shelby/

Usage:
  source venv/bin/activate
  python src/presence_agent.py
"""

import time
import os
import glob
import json
import cv2
import face_recognition
import paho.mqtt.client as mqtt
from picamera2 import Picamera2
from datetime import datetime

AGENT_ID = "serpi5v2"
ROOM = "entry_way"
MQTT_HOST = "localhost"
MQTT_PORT = 1883
MQTT_BASE = "pp/v1"


def iso_now():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def mqtt_topic(*parts):
    return "/".join([MQTT_BASE, *parts])


def publish_json(client, topic, payload, retain=False):
    client.publish(topic, json.dumps(payload), qos=1, retain=retain)


def load_known_faces(base_dir="faces"):
    known_encodings = []
    known_names = []

    for person_name in os.listdir(base_dir):
        person_dir = os.path.join(base_dir, person_name)
        if not os.path.isdir(person_dir):
            continue

        image_files = []
        for ext in ("*.jpg", "*.jpeg", "*.png"):
            image_files.extend(glob.glob(os.path.join(person_dir, ext)))

        print(f"[LOAD] {person_name}: {len(image_files)} images")

        for img_path in image_files:
            image = face_recognition.load_image_file(img_path)
            locations = face_recognition.face_locations(image)
            if not locations:
                continue

            encodings = face_recognition.face_encodings(image, locations)
            if encodings:
                known_encodings.append(encodings[0])
                known_names.append(person_name)

    return known_encodings, known_names


def main():
    print("[BOOT] Starting Pi Face Presence Agent (MQTT enabled)")

    known_encodings, known_names = load_known_faces("faces")
    if not known_encodings:
        print("[ERROR] No training faces found.")
        return

    client = mqtt.Client()
    client.connect(MQTT_HOST, MQTT_PORT, 60)
    client.loop_start()

    # Publish agent online
    publish_json(client, mqtt_topic("system", "agent", "status"), {
        "agent_id": AGENT_ID,
        "state": "online",
        "timestamp": iso_now()
    }, retain=True)

    picam = Picamera2()
    config = picam.create_preview_configuration(main={"size": (640, 480)})
    picam.configure(config)
    picam.start()
    time.sleep(1.5)

    print("[RUN] Camera online. Presence detection active.")

    present = set()

    try:
        while True:
            frame = picam.capture_array()

            # Convert XBGR8888 (4 channels) → RGB (3 channels)
            rgb = frame[:, :, :3]           # drop alpha
            rgb = cv2.cvtColor(rgb, cv2.COLOR_BGR2RGB)

            face_locations = face_recognition.face_locations(rgb)
            face_encodings = face_recognition.face_encodings(rgb, face_locations)

            seen = set()

            for enc in face_encodings:
                distances = face_recognition.face_distance(known_encodings, enc)
                best = distances.argmin()
                if distances[best] < 0.5:
                    seen.add(known_names[best])

            # Arrivals
            for person in seen - present:
                print(f"[EVENT] {person} arrived")
                publish_json(client, mqtt_topic("people", person, "event"), {
                    "person": person,
                    "event": "arrived",
                    "room": ROOM,
                    "confidence": 0.8,
                    "timestamp": iso_now(),
                    "source": AGENT_ID
                })

            # Departures
            for person in present - seen:
                print(f"[EVENT] {person} departed")
                publish_json(client, mqtt_topic("people", person, "event"), {
                    "person": person,
                    "event": "departed",
                    "room": ROOM,
                    "confidence": 0.0,
                    "timestamp": iso_now(),
                    "source": AGENT_ID
                })

            present = seen

            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\n[STOP] Shutting down.")
    finally:
        picam.stop()
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
