"""Pi Face Presence — presence_agent.py

Future‑proof face presence + identity agent for Raspberry Pi.

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

Optional preview window (requires GUI):
  python src/presence_agent.py --show-preview
"""

from __future__ import annotations

import argparse
import glob
import os
import sys
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import cv2
import face_recognition

cap = cv2.VideoCapture("/dev/video0", cv2.CAP_V4L2)

cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"YUYV"))
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

if not cap.isOpened():
    print("[ERROR] Could not open USB camera at /dev/video0")
else:
    print("[RUN] USB camera online at /dev/video0.")


@dataclass
class KnownIdentity:
    name: str
    encodings: List


def find_identity_dirs(faces_dir: str) -> List[str]:
    """Return immediate subdirectories under faces_dir."""
    if not os.path.isdir(faces_dir):
        raise FileNotFoundError(
            f"Faces directory not found: {faces_dir}\n"
            "Create it like: mkdir -p faces/Camille faces/Shelby"
        )

    dirs = []
    for entry in sorted(os.listdir(faces_dir)):
        path = os.path.join(faces_dir, entry)
        if os.path.isdir(path) and not entry.startswith("."):
            dirs.append(path)
    return dirs


def load_known_identities(
    faces_dir: str,
    model: str = "hog",
) -> List[KnownIdentity]:
    """Load and encode all faces found under faces_dir/<Name>/*.jpg|png.

    model: "hog" (fast, CPU) or "cnn" (more accurate, slower; needs heavy compute)
    """
    identities: List[KnownIdentity] = []

    for person_dir in find_identity_dirs(faces_dir):
        name = os.path.basename(person_dir)
        image_paths = []
        for ext in ("*.jpg", "*.jpeg", "*.png", "*.webp"):
            image_paths.extend(glob.glob(os.path.join(person_dir, ext)))

        if not image_paths:
            print(f"[WARN] No images found for '{name}' in {person_dir}")
            continue

        encs = []
        for p in sorted(image_paths):
            try:
                img = face_recognition.load_image_file(p)
                # If the training image has multiple faces, we take the first.
                locs = face_recognition.face_locations(img, model=model)
                if not locs:
                    print(f"[WARN] No face found in training image: {p}")
                    continue
                enc = face_recognition.face_encodings(img, known_face_locations=locs)
                if not enc:
                    print(f"[WARN] Could not encode face in training image: {p}")
                    continue
                encs.append(enc[0])
            except Exception as e:
                print(f"[WARN] Failed to process {p}: {e}")

        if not encs:
            print(f"[WARN] No usable face encodings for '{name}'.")
            continue

        identities.append(KnownIdentity(name=name, encodings=encs))
        print(f"[OK] Loaded {len(encs)} face encodings for '{name}'")

    if not identities:
        raise RuntimeError(
            "No identities loaded. Add training photos under faces/<Name>/ and retry.\n"
            "Example: faces/Camille/1.jpg, faces/Shelby/1.jpg"
        )

    return identities


def flatten_encodings(identities: List[KnownIdentity]) -> Tuple[List, List[str]]:
    """Flatten list of identities into (encodings, labels) arrays."""
    all_encodings = []
    all_labels = []
    for ident in identities:
        for e in ident.encodings:
            all_encodings.append(e)
            all_labels.append(ident.name)
    return all_encodings, all_labels


def choose_best_match(
    face_encoding,
    known_encodings: List,
    known_labels: List[str],
    threshold: float,
) -> Tuple[str, float]:
    """Return (label, distance). Label is 'Unknown' if no match under threshold."""
    if not known_encodings:
        return "Unknown", 1.0

    distances = face_recognition.face_distance(known_encodings, face_encoding)
    best_i = int(distances.argmin())
    best_dist = float(distances[best_i])

    if best_dist <= threshold:
        return known_labels[best_i], best_dist
    return "Unknown", best_dist


def init_camera(width, height):
    cap = cv2.VideoCapture(0)

    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"YUYV"))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    if not cap.isOpened():
        print("[ERROR] Could not open USB camera")
        return None

    print("[RUN] USB camera online. Presence detection active.")
    return cap


def main() -> int:
    parser = argparse.ArgumentParser(description="Pi Face Presence — presence agent")
    parser.add_argument(
        "--faces-dir",
        default="faces",
        help="Directory containing faces/<Name>/*.jpg training images (default: faces)",
    )
    parser.add_argument(
        "--width", type=int, default=640, help="Camera capture width (default: 640)"
    )
    parser.add_argument(
        "--height", type=int, default=480, help="Camera capture height (default: 480)"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.50,
        help="Face match threshold (lower = stricter). Typical: 0.45–0.60 (default: 0.50)",
    )
    parser.add_argument(
        "--model",
        choices=["hog", "cnn"],
        default="hog",
        help="Face location model: hog (fast) or cnn (slower, more accurate) (default: hog)",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=0.35,
        help="Seconds between recognition loops (default: 0.35)",
    )
    parser.add_argument(
        "--show-preview",
        action="store_true",
        help="Show a live preview window (may not work over some remote sessions)",
    )

    args = parser.parse_args()

    identities = load_known_identities(args.faces_dir, model=args.model)
    known_encodings, known_labels = flatten_encodings(identities)

    picam = init_camera(args.width, args.height)

    last_printed: Optional[str] = None
    last_print_time = 0.0

    print("\n[RUN] Starting recognition. Press Ctrl+C to stop.")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("[WARN] Failed to read frame")
                time.sleep(0.5)
                continue

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # Detect faces and compute encodings
            face_locations = face_recognition.face_locations(rgb, model=args.model)
            face_encodings = face_recognition.face_encodings(rgb, face_locations)

            labels_this_frame: List[str] = []
            for enc, (top, right, bottom, left) in zip(face_encodings, face_locations):
                label, dist = choose_best_match(enc, known_encodings, known_labels, args.threshold)
                labels_this_frame.append(label)

                if args.show_preview:
                    cv2.rectangle(bgr, (left, top), (right, bottom), (0, 255, 0), 2)
                    cv2.putText(
                        bgr,
                        f"{label}",
                        (left, max(0, top - 10)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 255, 0),
                        2,
                    )

            # Print a simple presence line when the identity set changes
            # (debounced so it doesn't spam the terminal)
            now = time.time()
            if labels_this_frame:
                # If multiple faces, print comma-separated unique labels
                current = ", ".join(sorted(set(labels_this_frame)))
            else:
                current = "No face"

            if current != last_printed and (now - last_print_time) > 0.6:
                print(f"[PRESENCE] {current}")
                last_printed = current
                last_print_time = now

            if args.show_preview:
                cv2.imshow("Pi Face Presence", bgr)
                if cv2.waitKey(1) & 0xFF == 27:
                    break

            time.sleep(args.interval)

    except KeyboardInterrupt:
        print("\n[STOP] Keyboard interrupt — shutting down.")
    finally:
        try:
            cap.release()
        except Exception:
            pass
        if args.show_preview:
            cv2.destroyAllWindows()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
