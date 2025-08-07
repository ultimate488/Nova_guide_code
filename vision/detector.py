# nova_guide/vision/detector.py

import cv2
import time
from ultralytics import YOLO
from .object_mapper import map_object_to_alert

# ❌ We have REMOVED pyttsx3 and the speak_async function from this file.

class ObjectDetectorProcess:
    """
    A class that encapsulates the object detection logic.
    Its ONLY job is to continuously update a shared flag.
    """
    def __init__(self, model_name="yolov8n.pt"):
        print("🧠 [VISION] Initializing Object Detector...")
        self.model = self._load_yolo_model(model_name)
        self.cap = None

    def _load_yolo_model(self, model_name):
        try:
            model = YOLO(model_name)
            print(f"🧠 [VISION] Successfully loaded model: {model_name}")
            return model
        except Exception as e:
            print(f"Error loading YOLO model '{model_name}': {e}")
            return None

    def _init_camera(self):
        for camera_index in range(3):
            cap = cv2.VideoCapture(camera_index)
            time.sleep(1)
            if cap.isOpened():
                print(f"🧠 [VISION] Successfully opened camera at index {camera_index}.")
                return cap
            cap.release()
        print("Error: Could not open any webcam.")
        return None

    def run(self, shared_obstacle_flag, stop_event):
        """
        The main loop for the vision process.
        It continuously updates the shared boolean flag.
        """
        self.cap = self._init_camera()
        if not self.cap or not self.model:
            shared_obstacle_flag.value = False
            return

        critical_objects = {'Human', 'Chair', 'Door', 'Obstacle'}

        while not stop_event.is_set():
            ret, frame = self.cap.read()
            if not ret:
                break

            results = self.model(frame, verbose=False)[0]

            detected_alerts = set()
            for r in results.boxes:
                label = self.model.names[int(r.cls[0])]
                confidence = r.conf[0]

                alert_text = map_object_to_alert(label)
                if alert_text and confidence > 0.7:
                    detected_alerts.add(alert_text)

            # CORE LOGIC: Update the shared flag based on current detections.
            if not critical_objects.isdisjoint(detected_alerts):
                shared_obstacle_flag.value = True
            else:
                shared_obstacle_flag.value = False

            # --- Visual Display Logic (can be commented out for performance) ---
            # This part remains the same.
            for r in results.boxes:
                label = self.model.names[int(r.cls[0])]
                confidence = r.conf[0]
                x1, y1, x2, y2 = map(int, r.xyxy[0])
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, f'{label} {confidence:.2f}', (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

            cv2.imshow("Nova-Guide Vision", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                stop_event.set()
            # --- End Visual Display Logic ---

        shared_obstacle_flag.value = False
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()
        print("🧠 [VISION] Vision process stopped.")