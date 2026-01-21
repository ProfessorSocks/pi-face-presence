# Running Pi Face Presence (Quick Reference)

This file contains the exact steps to start the camera and run the face‑presence test on your Raspberry Pi.

---

## 1. Test the Camera (RPiCam)

This confirms the Raspberry Pi camera is working at the system level.

```bash
rpicam-hello
```

To take a still photo:

```bash
rpicam-still -o test.jpg
```

To record a short video (5 seconds):

```bash
rpicam-vid -t 5000 -o test.h264
```

---

## 2. Go to the Project Folder

```bash
cd ~/presence_ai
```
(or `cd ~/presence_ai2` if that is the folder you used)

---

## 3. Activate the Python Virtual Environment

```bash
source venv/bin/activate
```

You should see `(venv)` at the beginning of your terminal prompt.

---

## 4. Run the Face Detection Script

```bash
python test_face.py
```

If your file is named differently (for example `test_face_picamera2.py`), run:

```bash
python test_face_picamera2.py
```

---

## 5. Exit the Program

To close the camera window and stop the program:

- Press **ESC** in the camera window, or
- Press **Ctrl + C** in the terminal

---

## 6. Full Start‑Up Sequence (Copy/Paste)

```bash
cd ~/presence_ai
source venv/bin/activate
python test_face.py
```

---

This file is intended as a quick operational checklist so you can restart your Pi Face Presence system at any time without re‑reading setup documentation.

