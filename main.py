# nova_guide/main.py

import time
import random
import sys
import os
from threading import Event
import multiprocessing
from queue import Empty
import cv2

# Ensure the project root is in the path for module imports
sys.path.append(os.path.dirname(__file__))

# Import the REAL voice recognizer!
try:
    from voice.recognizer import VoiceRecognizer
except ImportError:
    print("Error: Could not import VoiceRecognizer. Ensure 'voice/recognizer.py' exists and dependencies are installed.")
    print("Falling back to dummy voice command class.")
    class VoiceRecognizer:
        def __init__(self):
            print("🎙️ [DUMMY] Voice Recognizer Initialized.")
        def listen_for_command(self):
            commands = ["go to kitchen", "go to bathroom", "go outside", "stop", "help"]
            command = random.choice(commands)
            print(f"🔊 [DUMMY] Listening... I heard: '{command}'")
            return command


# Import the REAL voice feedback system!
try:
    from voice.tts import VoiceFeedback
except ImportError:
    print("Error: Could not import VoiceFeedback. Ensure 'voice/tts.py' exists and dependencies are installed.")
    print("Falling back to dummy voice feedback class.")
    class VoiceFeedback:
        def say(self, text):
            print(f"🎤 [DUMMY] FEEDBACK: {text}")

# Import the REAL wake word detector!
try:
    from voice.wakeword import WakeWordDetector
except ImportError as e:
    print(f"Error: Could not import WakeWordDetector. {e}")
    print("Falling back to dummy wake word logic.")
    class WakeWordDetector:
        def __init__(self, *args, **kwargs):
            pass
        def start(self):
            print("👁️ [DUMMY] Wake word detection started.")
        def join(self):
            print("👁️ [DUMMY] Wake word detection joined.")
            
# Import the new, more detailed MotorController
from control.motors import MotorController

# --- NEW: Import our vision process module ---
from vision.detector import ObjectDetectorProcess


# --- Dummy Classes for Simulation ---
class SensorManager:
    """A dummy class to simulate sensor readings."""
    def get_ultrasonic_reading(self):
        if random.random() > 0.9:
            return random.uniform(50.0, 100.0)
        return random.uniform(10.0, 30.0)
    def get_gps_location(self):
        if random.random() > 0.3:
            return (random.uniform(20.0, 21.0), random.uniform(70.0, 71.0))
        return None

# --- Main Robot Logic ---

class Robot:
    def __init__(self):
        self.voice_command = VoiceRecognizer()
        self.voice_feedback = VoiceFeedback()
        self.motor_controller = MotorController()
        self.sensor_manager = SensorManager()
        self.mode = "indoor"
        self.room_locations = {"kitchen": (2.3, 5.0), "bathroom": (1.1, 1.1)}
        self.wake_word_event = Event()
        self.wake_word_detector = WakeWordDetector(self.wake_word_event)
        
        self.vision_queue = multiprocessing.Queue()
        self.vision_stop_event = multiprocessing.Event()
        
        self.object_detector_instance = ObjectDetectorProcess()
        self.vision_process = multiprocessing.Process(
            target=self.object_detector_instance.run, 
            args=(self.vision_queue, self.vision_stop_event),
            daemon=True
        )

        self.is_stopped_by_vision = False # True if robot is stopped due to an obstacle
        self.critical_obstacle_present = False # True if a critical obstacle is currently detected by vision
        self.last_stopped_message_time = 0 # For spamming "Robot stopped" message
        self.stopped_message_cooldown = 3 # seconds
    
    def process_command(self, command):
        """Processes a recognized voice command and triggers the right action."""
        command = command.lower().strip()
        print(f"Processing command: '{command}'")

        # Commands that should allow the robot to move again
        movement_commands = ["go to", "kitchen", "bathroom", "outside", "turn left", "turn right"]
        if any(cmd in command for cmd in movement_commands):
            # Only allow movement if no critical obstacle is currently present
            if not self.critical_obstacle_present:
                self.is_stopped_by_vision = False # Clear the vision stop state
                # Original movement logic
                if "go to" in command:
                    destination = command.replace("go to ", "").strip()
                    if destination in self.room_locations:
                        self.mode = "indoor"
                        print(f"🧠 DECISION: Switched to Indoor Mode. Navigating to {destination}.")
                        self.voice_feedback.say(f"Navigating to the {destination}.")
                        self.motor_controller.move_forward(speed=50)
                    else:
                        self.voice_feedback.say(f"I don't know where the {destination} is.")

                elif "kitchen" in command:
                    self.mode = "indoor"
                    self.voice_feedback.say("Navigating to the kitchen.")
                    self.motor_controller.move_forward(speed=50)
                
                elif "bathroom" in command:
                    self.mode = "indoor"
                    self.voice_feedback.say("Navigating to the bathroom.")
                    self.motor_controller.move_forward(speed=50)

                elif "outside" in command:
                    self.mode = "outdoor"
                    print("🧠 DECISION: Switched to Outdoor Mode.")
                    self.voice_feedback.say("Switching to outdoor mode. Please wait for GPS lock.")
                    self.motor_controller.move_forward(speed=50)

                elif "turn left" in command:
                    self.motor_controller.turn_left()
                    self.voice_feedback.say("Turning left.")

                elif "turn right" in command:
                    self.motor_controller.turn_right()
                    self.voice_feedback.say("Turning right.")
            else:
                self.voice_feedback.say("I cannot move, there is an obstacle in my path.")
                print("🧠 DECISION: Movement command ignored due to critical obstacle.")
            
        elif "stop" in command:
            self.is_stopped_by_vision = True # A manual stop also sets the stop state
            self.motor_controller.stop()
            self.voice_feedback.say("Stopping.")

        elif "help" in command:
            self.voice_feedback.say("I can help you navigate. Try saying 'Go to kitchen' or 'Go outside'.")
        
        else:
            self.voice_feedback.say("Command not recognized.")

    def check_vision_queue(self):
        """
        Checks the queue for new vision alerts from the vision process without blocking.
        Updates the robot's state based on critical obstacles.
        """
        new_alerts = []
        try:
            while True: # Read all available alerts from the queue
                alert = self.vision_queue.get_nowait()
                new_alerts.append(alert)
        except Empty:
            pass # No more alerts in the queue

        if new_alerts:
            # Flatten the list of lists into a single set of unique alerts
            all_current_alerts = set(item for sublist in new_alerts for item in sublist)
            
            # Determine if any critical obstacles are present from the latest alerts
            # For now, 'Human' is considered critical. Add 'Stairs', 'Pothole' etc. later.
            critical_obstacles_detected_now = 'Human' in all_current_alerts or 'Stairs' in all_current_alerts # Add other critical alerts here

            # --- Logic to stop the robot ---
            if critical_obstacles_detected_now and not self.is_stopped_by_vision:
                print(f"🚨 [ALERT] Critical obstacle detected: {list(all_current_alerts)}")
                print("🚨 [DECISION] Stopping motors due to critical obstacle.")
                self.voice_feedback.say("Obstacle detected. Stopping now.")
                self.motor_controller.stop()
                self.is_stopped_by_vision = True # Set the state to stopped by vision
                self.critical_obstacle_present = True # Mark that a critical obstacle is indeed present
                self.last_stopped_message_time = time.time() # Reset message cooldown

            # --- Logic to resume the robot ---
            elif not critical_obstacles_detected_now and self.is_stopped_by_vision and self.critical_obstacle_present:
                # Only resume if it was stopped by vision AND the critical obstacle is no longer present
                print("✅ [DECISION] Critical obstacle cleared. Resuming normal operation.")
                self.voice_feedback.say("Path clear. Ready for commands.")
                self.is_stopped_by_vision = False # Clear the vision stop state
                self.critical_obstacle_present = False # No critical obstacle currently present
                self.motor_controller.stop() # Ensure it's truly stopped before resuming movement via command
                
            # Update the critical_obstacle_present flag based on the latest vision data
            self.critical_obstacle_present = critical_obstacles_detected_now
        
    def cleanup(self):
        """Ensures all resources are released gracefully upon program exit."""
        self.motor_controller.cleanup()
        
        self.wake_word_detector.stop()
        self.wake_word_detector.join()
        
        self.vision_stop_event.set()
        self.vision_process.join(timeout=5)
        if self.vision_process.is_alive():
            print("Warning: Vision process did not terminate gracefully. Terminating forcefully.")
            self.vision_process.terminate()
        
        if hasattr(self.voice_feedback, 'stop'):
            self.voice_feedback.stop()

        cv2.destroyAllWindows()


    def run(self):
        """The main loop for the robot's behavior."""
        print("--- Starting NOVA-GUIDE Simulation ---")
        
        print("Starting Vision process...")
        self.vision_process.start()
        
        self.voice_feedback.say("NOVA guide simulation started. Listening for NOVA.")
        self.wake_word_detector.start()
        
        while True:
            # Always check the vision queue to get the latest obstacle information
            self.check_vision_queue()

            if not self.is_stopped_by_vision:
                # If not stopped by vision, proceed with normal operation
                print("Main thread waiting for wake word...")
                self.wake_word_event.wait() # This will block until wake word is detected
                
                self.wake_word_event.clear() # Reset the event for the next detection
                
                print("Wake word received. Listening for a command...")
                self.voice_feedback.say("Yes?")
                
                command = self.voice_command.listen_for_command() # This will block while listening
                
                if command:
                    self.process_command(command)
                    
                # Re-start the wake word detector after a command is processed
                self.wake_word_detector = WakeWordDetector(self.wake_word_event)
                self.wake_word_detector.start()
            else:
                # If stopped by vision, inform the user (with cooldown) and wait for obstacle to clear or manual command
                if time.time() - self.last_stopped_message_time > self.stopped_message_cooldown:
                    self.voice_feedback.say("Obstacle detected. Please clear my path or give a new command.")
                    print("Robot stopped by vision. Awaiting obstacle clear or new command.")
                    self.last_stopped_message_time = time.time()
                
                # Even when stopped by vision, we still allow wake word detection and command listening
                # This ensures the user can always say "stop" or "resume"
                # The `process_command` will handle if movement commands are allowed while obstacle is present
                print("Main thread waiting for wake word (while stopped)...")
                self.wake_word_event.wait(timeout=0.5) # Use a timeout to allow periodic vision checks
                
                if self.wake_word_event.is_set():
                    self.wake_word_event.clear()
                    print("Wake word received (while stopped). Listening for a command...")
                    self.voice_feedback.say("Yes?")
                    command = self.voice_command.listen_for_command()
                    if command:
                        self.process_command(command)
                    self.wake_word_detector = WakeWordDetector(self.wake_word_event)
                    self.wake_word_detector.start()
                
            # Sensor readings can happen continuously regardless of robot state
            self.sensor_manager.get_ultrasonic_reading()
            self.sensor_manager.get_gps_location()
            
            # Small delay to prevent burning CPU in the main loop
            time.sleep(0.1)

if __name__ == "__main__":
    my_robot = Robot()
    try:
        my_robot.run()
    except KeyboardInterrupt:
        print("\n--- Simulation stopped by user. ---")
    finally:
        my_robot.cleanup()
