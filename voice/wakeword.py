# voice/wakeword.py

import os
import sys
import pvporcupine
from pvporcupine import Porcupine
from pvrecorder import PvRecorder
from threading import Thread, Event
import time

# Import the AccessKey and model path from our config file
from config import PICOVOICE_ACCESS_KEY, NOVA_WAKE_WORD_MODEL_PATH, PICOVOICE_SENSITIVITY

class WakeWordDetector(Thread):
    """
    A class to detect a wake word using Picovoice Porcupine.
    This runs in its own thread, continuously listening for the wake word.
    When the wake word is detected, it sets a threading.Event.
    """
    def __init__(self, wake_word_detected_event):
        super().__init__()
        self.wake_word_detected_event = wake_word_detected_event
        self.porcupine = None
        self.recorder = None
        self.is_listening = True

        try:
            self.porcupine = pvporcupine.create(
                access_key=PICOVOICE_ACCESS_KEY,
                keyword_paths=[NOVA_WAKE_WORD_MODEL_PATH],
                sensitivities=[PICOVOICE_SENSITIVITY]
            )
            
            self.recorder = PvRecorder(
                frame_length=self.porcupine.frame_length,
                device_index=-1 # Use the default microphone
            )
            
            print(f"👁️ Wake Word Detector Initialized. Listening for 'NOVA' with sensitivity {PICOVOICE_SENSITIVITY}...")

        except Exception as e:
            print(f"Error initializing Porcupine or PvRecorder: {e}")
            self.porcupine = None
            
    def run(self):
        """Main loop for the thread."""
        if not self.porcupine or not self.recorder:
            print("Engine or recorder is not initialized. Cannot start listening.")
            return

        print(f"Starting continuous listening for wake word 'NOVA'...")
        try:
            self.recorder.start()
            while self.is_listening:
                pcm = self.recorder.read()
                result = self.porcupine.process(pcm)

                if result >= 0:
                    print(f"🚨 Wake word 'NOVA' detected!")
                    self.wake_word_detected_event.set()
                    self.is_listening = False
                    
        except Exception as e:
            print(f"Error in wake word audio stream: {e}", file=sys.stderr)

    def stop(self):
        """Stops the listening thread gracefully."""
        self.is_listening = False
        if self.recorder:
            self.recorder.stop()
            
    def __del__(self):
        """Cleans up the resources."""
        if self.porcupine:
            self.porcupine.delete()
        if self.recorder:
            self.recorder.delete()