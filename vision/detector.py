# nova_guide/vision/detector.py

"""
Object Detection Process for the Nova-Guide Project.

This module provides a standalone process for object detection, running in parallel
with the main robot control loop. It captures video frames, performs detection,
displays the output, and sends alerts back to the main process via a queue.

Optimization:
- Alerts are only sent when the detected objects change.
- The confidence threshold for an object to be considered is increased to 0.7
  to reduce false positives.
"""

import cv2
import time
from ultralytics import YOLO
import multiprocessing
import threading
from .object_mapper import map_object_to_alert

# We'll use a thread-safe TTS engine for speaking
import pyttsx3
tts_engine = pyttsx3.init()

def speak_async(text):
    """
    Function to speak a text string in a non-blocking thread.
    """
    def _speak_target(t):
        try:
            tts_engine.say(t)
            tts_engine.runAndWait()
        except Exception as e:
            print(f"Error in TTS thread: {e}")
            
    thread = threading.Thread(target=_speak_target, args=(text,))
    thread.daemon = True
    thread.start()


class ObjectDetectorProcess:
    """
    A class that encapsulates the object detection logic to be run as a separate process.
    """
    def __init__(self, model_name="yolov8n.pt"):
        print("🧠 [VISION] Initializing Object Detector...")
        self.model = self._load_yolo_model(model_name)
        self.cap = None
        self.last_spoken_time = 0
        self.spoken_cooldown = 5 # seconds to wait before speaking the same object again

    def _load_yolo_model(self, model_name):
        """Internal helper to load the YOLO model."""
        try:
            model = YOLO(model_name)
            print(f"🧠 [VISION] Successfully loaded model: {model_name}")
            return model
        except Exception as e:
            print(f"Error loading YOLO model '{model_name}': {e}")
            print("Vision module will not be available.")
            return None

    def _init_camera(self):
        """Internal helper to initialize the camera with better error handling."""
        for camera_index in range(3): # Try camera indices 0, 1, 2
            cap = cv2.VideoCapture(camera_index)
            time.sleep(1) # Give the camera a moment to initialize
            if cap.isOpened():
                print(f"🧠 [VISION] Successfully opened camera at index {camera_index}.")
                return cap
            else:
                print(f"🧠 [VISION] Failed to open camera at index {camera_index}.")
                cap.release()
        
        print("Error: Could not open any webcam. Please check your camera connection and permissions.")
        return None

    def run(self, detection_queue, stop_event):
        """
        The main loop for the object detection process.
        """
        self.cap = self._init_camera()
        if not self.cap or not self.model:
            return

        last_sent_alerts = set()
        last_spoken_object = None
        
        while not stop_event.is_set():
            ret, frame = self.cap.read()
            if not ret:
                break

            results = self.model(frame, verbose=False)[0]
            
            alerts = set()
            for r in results.boxes:
                label = self.model.names[int(r.cls[0])]
                confidence = r.conf[0]
                
                alert_text = map_object_to_alert(label)
                # We increased the confidence threshold here to reduce false positives
                if alert_text and confidence > 0.7: 
                    alerts.add(alert_text)
            
            if alerts != last_sent_alerts:
                detection_queue.put(list(alerts))
                last_sent_alerts = alerts

            current_object = " ".join(sorted(list(alerts)))
            if current_object and current_object != last_spoken_object and time.time() - self.last_spoken_time > self.spoken_cooldown:
                speak_async(f"{current_object} ahead")
                self.last_spoken_time = time.time()
                last_spoken_object = current_object

            for r in results.boxes:
                label = self.model.names[int(r.cls[0])]
                confidence = r.conf[0]
                x1, y1, x2, y2 = map(int, r.xyxy[0])
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, f'{label} {confidence:.2f}', (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            cv2.imshow("Nova-Guide Vision", frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                stop_event.set()
        
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()
        print("🧠 [VISION] Vision process stopped.")
