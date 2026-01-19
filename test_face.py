from picamera2 import Picamera2
import cv2
import face_recognition
import time

picam = Picamera2()
config = picam.create_preview_configuration(main={"size": (640, 480)})
picam.configure(config)
picam.start()

time.sleep(2)

while True:
    frame = picam.capture_array()
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    faces = face_recognition.face_locations(rgb)

    print("Faces detected:", len(faces))
    cv2.imshow("Presence Camera", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cv2.destroyAllWindows()
picam.stop()
