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
import cv2
import face_recognition
from picamera2 import Picamera2


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
    print("[BOOT] Starting Pi Face Presence Agent")

    known_encodings, known_names = load_known_faces("faces")

    if not known_encodings:
        print("[ERROR] No training faces found in faces/ folder.")
        return

    print(f"[OK] Loaded {len(known_encodings)} face encodings")

    picam = Picamera2()
    config = picam.create_preview_configuration(main={"size": (640, 480)})
    picam.configure(config)
    picam.start()

    time.sleep(1.5)
    print("[RUN] Camera online. Press Ctrl+C to stop.")

    last_seen = None

    try:
        while True:
            frame = picam.capture_array()
            rgb = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

            face_locations = face_recognition.face_locations(rgb)
            face_encodings = face_recognition.face_encodings(rgb, face_locations)

            current_names = []

            for face_encoding in face_encodings:
                distances = face_recognition.face_distance(known_encodings, face_encoding)
                best_match_index = distances.argmin()

                if distances[best_match_index] < 0.5:
                    name = known_names[best_match_index]
                else:
                    name = "Unknown"

                current_names.append(name)

            if current_names:
                label = ", ".join(set(current_names))
            else:
                label = "No face"

            if label != last_seen:
                print(f"[PRESENCE] {label}")
                last_seen = label

            time.sleep(0.3)

    except KeyboardInterrupt:
        print("\n[STOP] Shutting down...")

    finally:
        picam.stop()


if __name__ == "__main__":
    main()
