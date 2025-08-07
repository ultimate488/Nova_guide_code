# nova_guide/main.py

import time
import multiprocessing
from multiprocessing import Queue
from threading import Event
import sys
import os
import cv2

# --- Module Imports ---
try:
    from voice.recognizer import VoiceRecognizer
    # ✅ We now import the AudioProcess server
    from voice.tts import AudioProcess
    from voice.wakeword import WakeWordDetector
    from control.motors import MotorController
    from vision.detector import ObjectDetectorProcess
except ImportError as e:
    print(f"CRITICAL ERROR importing a module: {e}. Please ensure all files exist.")
    sys.exit(1)


class Robot:
    def __init__(self):
        print("🤖 Initializing NOVA-GUIDE...")
        # ✅ GENIUS FIX: Create a single, shared queue for all audio requests.
        self.audio_queue = Queue()

        # --- Process and Thread Initialization ---
        self.audio_process = AudioProcess(self.audio_queue)
        self.voice_command = VoiceRecognizer()
        self.motor_controller = MotorController()
        self.wake_word_event = Event()
        self.wake_word_detector = None # Will be created in the run loop
        self.vision_obstacle_detected = multiprocessing.Value('b', False)
        self.vision_stop_event = multiprocessing.Event()
        self.object_detector_instance = ObjectDetectorProcess()
        self.vision_process = multiprocessing.Process(
            target=self.object_detector_instance.run,
            args=(self.vision_obstacle_detected, self.vision_stop_event),
            daemon=True
        )

        # --- State Machine & Task Memory ---
        self.is_stopped_by_vision = False
        self.current_task = None
        self.last_time_obstacle_was_seen = 0.0
        self.clear_duration_threshold = 2.0

    def say(self, text):
        """A simple helper to put text on the audio queue."""
        print(f"Queueing for TTS: '{text}'")
        self.audio_queue.put(text)

    def process_command(self, command):
        """Processes a voice command and sets the robot's current task."""
        command = command.lower().strip() if command else ""
        is_path_blocked = self.is_stopped_by_vision

        if "kitchen" in command:
            if not is_path_blocked:
                self.current_task = {'action': 'move_forward', 'speed': 50}
                self.say("Okay, going to the kitchen.")
                self.motor_controller.move_forward(speed=50)
            else:
                self.say("I cannot go to the kitchen, my path is blocked.")
        elif "stop" in command:
            self.current_task = None
            self.motor_controller.stop()
            self.say("Stopping all movement and cancelling task.")

    def resume_current_task(self):
        """Resumes a task from memory if one exists."""
        if not self.current_task: return
        self.say("Resuming my task.")
        action = self.current_task.get('action')
        if action == 'move_forward':
            self.motor_controller.move_forward(speed=self.current_task.get('speed', 50))

    def check_obstacle_state(self):
        """The robust state checker with task resumption logic."""
        is_obstacle_seen_now = self.vision_obstacle_detected.value

        if is_obstacle_seen_now:
            self.last_time_obstacle_was_seen = time.time()
            if not self.is_stopped_by_vision:
                self.is_stopped_by_vision = True
                self.motor_controller.stop()
                self.say("Obstacle detected. Pausing task.")
        elif self.is_stopped_by_vision:
            time_since_last_sighting = time.time() - self.last_time_obstacle_was_seen
            if time_since_last_sighting >= self.clear_duration_threshold:
                self.is_stopped_by_vision = False
                # ✅ Restored the missing print statement for clarity
                print("✅ [DECISION] Path is clear.")
                self.say("Path clear.")
                time.sleep(1.0) # Give TTS time to speak before motors start
                if self.current_task:
                    self.resume_current_task()

    def cleanup(self):
        print("\n--- Cleaning up resources... ---")
        self.motor_controller.cleanup()
        if self.wake_word_detector and self.wake_word_detector.is_alive():
            self.wake_word_detector.stop()
            self.wake_word_detector.join()
        self.vision_stop_event.set()
        if self.vision_process.is_alive(): self.vision_process.join(timeout=2)
        # ✅ GENIUS FIX: Signal the audio process to shut down.
        self.audio_queue.put(None)
        if self.audio_process.is_alive(): self.audio_process.join(timeout=2)
        cv2.destroyAllWindows()
        print("--- Cleanup Complete. ---")

    def run(self):
        print("--- Starting NOVA-GUIDE: The Legendary Build ---")
        self.vision_process.start()
        self.audio_process.start()
        self.say("System initiated. Say my name to give a command.")

        self.wake_word_detector = WakeWordDetector(self.wake_word_event)
        self.wake_word_detector.start()

        try:
            while True:
                self.check_obstacle_state()
                if self.wake_word_event.wait(timeout=0.1):
                    self.wake_word_event.clear()
                    self.wake_word_detector.join()
                    self.say("Yes?")
                    command = self.voice_command.listen_for_command()
                    if command: self.process_command(command)
                    self.wake_word_detector = WakeWordDetector(self.wake_word_event)
                    self.wake_word_detector.start()
        except KeyboardInterrupt:
            print("\n--- User initiated shutdown. ---")
        finally:
            self.cleanup()


if __name__ == "__main__":
    my_robot = Robot()
    my_robot.run()