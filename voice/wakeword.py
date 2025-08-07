# voice/wakeword.py

import os
import sys
import pvporcupine
from pvrecorder import PvRecorder
from threading import Thread, Event
import time

# Assuming config.py has your keys and paths
try:
    from config import PICOVOICE_ACCESS_KEY, NOVA_WAKE_WORD_MODEL_PATH, PICOVOICE_SENSITIVITY
except ImportError:
    print("Error: Could not import from config.py. Please ensure it exists and is configured.")
    # Provide dummy values to prevent crashing if config is missing
    PICOVOICE_ACCESS_KEY = "YOUR_ACCESS_KEY_HERE"
    NOVA_WAKE_WORD_MODEL_PATH = "" 
    PICOVOICE_SENSITIVITY = 0.5


class WakeWordDetector(Thread):
    """
    A "single-shot" thread to detect a wake word.
    When detected, it sets an event and then terminates itself cleanly,
    releasing all audio resources.
    """
    def __init__(self, wake_word_detected_event):
        super().__init__()
        self.wake_word_detected_event = wake_word_detected_event
        self.porcupine = None
        self.recorder = None
        self.is_listening = True

        try:
            if not NOVA_WAKE_WORD_MODEL_PATH:
                raise ValueError("Wake word model path is not set in config.py")
            
            self.porcupine = pvporcupine.create(
                access_key=PICOVOICE_ACCESS_KEY,
                keyword_paths=[NOVA_WAKE_WORD_MODEL_PATH],
                sensitivities=[PICOVOICE_SENSITIVITY]
            )
            self.recorder = PvRecorder(
                frame_length=self.porcupine.frame_length,
                device_index=-1
            )
        except Exception as e:
            print(f"Error initializing Porcupine: {e}")
            self.porcupine = None

    def run(self):
        """Main loop for the thread. Runs until wake word is found or stop() is called."""
        if not self.porcupine or not self.recorder:
            print("Wake word engine not initialized. Cannot listen.")
            return

        print(f"Starting listening for wake word 'NOVA'...")
        try:
            self.recorder.start()
            while self.is_listening:
                pcm = self.recorder.read()
                result = self.porcupine.process(pcm)
                if result >= 0:
                    print(f"🚨 Wake word 'NOVA' detected!")
                    self.wake_word_detected_event.set()
                    self.is_listening = False # Exit the loop
        except Exception as e:
            print(f"Error in wake word audio stream: {e}", file=sys.stderr)
        finally:
            # ✅ GENIUS FIX 4: This block ALWAYS runs, guaranteeing resource release.
            if self.recorder:
                self.recorder.stop()
                self.recorder.delete()
            if self.porcupine:
                self.porcupine.delete()
            print("Wake word listener thread finished and resources released.")

    def stop(self):
        """Public method to signal the listening loop to stop from outside."""
        self.is_listening = False