#!/usr/bin/env python3
import os
import time
import argparse
from pathlib import Path

import cv2
import face_recognition
import paho.mqtt.client as mqtt


def load_known_faces(faces_dir):
    known_encodings = []
    known_names = []

    faces_path = Path(faces_dir)

    if not faces_path.exists():
        print(f"[ERROR] Faces folder not found: {faces_dir}")
        return known_encodings, known_names

    for person_dir in faces_path.iterdir():
        if not person_dir.is_dir():
            continue

        name = person_dir.name

        for img_path in person_dir.glob("*"):
            if img_path.suffix.lower() not in [".jpg", ".jpeg", ".png"]:
                continue

            image = face_recognition.load_image_file(str(img_path))
            locations = face_recognition.face_locations(image)

            if len(locations) == 0:
                print(f"[WARN] No face found in training image: {img_path}")
                continue

            encoding = face_recognition.face_encodings(image, locations)[0]
            known_encodings.append(encoding)
            known_names.append(name)

            print(f"[LOAD] Loaded face for {name}: {img_path}")

    return known_encodings, known_names


def connect_mqtt(host, port):
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.connect(host, port, 60)
    client.loop_start()
    print(f"[MQTT] Connected to {host}:{port}")
    return client


def publish_event(client, base_topic, name, event):
    topic = f"{base_topic}/people/{name}/event"
    payload = event
    client.publish(topic, payload, retain=False)
    print(f"[MQTT] {topic} -> {payload}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--camera", type=int, default=0)
    parser.add_argument("--faces", default="faces")
    parser.add_argument("--mqtt-host", default="localhost")
    parser.add_argument("--mqtt-port", type=int, default=1883)
    parser.add_argument("--base-topic", default="pp/v1")
    parser.add_argument("--width", type=int, default=640)
    parser.add_argument("--height", type=int, default=480)
    parser.add_argument("--tolerance", type=float, default=0.55)
    parser.add_argument("--cooldown", type=int, default=30)
    args = parser.parse_args()

    known_encodings, known_names = load_known_faces(args.faces)

    if not known_encodings:
        print("[ERROR] No usable training faces loaded.")
        print("[FIX] Add clear face photos inside faces/Name/")
        return 1

    mqtt_client = connect_mqtt(args.mqtt_host, args.mqtt_port)

    cap = cv2.VideoCapture(args.camera)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"YUYV"))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)

    if not cap.isOpened():
        print(f"[ERROR] Could not open USB camera index {args.camera}")
        return 1

    print(f"[RUN] USB camera online on index {args.camera}")
    print("[RUN] Press CTRL+C to stop")

    last_seen = {}

    try:
        while True:
            ret, frame = cap.read()

            if not ret:
                print("[WARN] Failed to read frame")
                time.sleep(1)
                continue

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            locations = face_recognition.face_locations(rgb)
            encodings = face_recognition.face_encodings(rgb, locations)

            seen_this_frame = set()

            for encoding in encodings:
                matches = face_recognition.compare_faces(
                    known_encodings,
                    encoding,
                    tolerance=args.tolerance
                )

                name = None

                if True in matches:
                    match_index = matches.index(True)
                    name = known_names[match_index]

                if name:
                    seen_this_frame.add(name)
                    now = time.time()
                    previous = last_seen.get(name, 0)

                    if now - previous > args.cooldown:
                        publish_event(mqtt_client, args.base_topic, name, "seen")

                    last_seen[name] = now
                    print(f"[FACE] Saw {name}")

            time.sleep(1)

    except KeyboardInterrupt:
        print("\n[STOP] Stopping presence agent")

    finally:
        cap.release()
        mqtt_client.loop_stop()
        mqtt_client.disconnect()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())