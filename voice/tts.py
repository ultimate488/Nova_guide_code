# voice/tts.py

import pyttsx3

class VoiceFeedback:
    """
    A class to handle text-to-speech (TTS) for giving vocal feedback.
    Uses the pyttsx3 library which works offline.
    """
    def __init__(self):
        """Initializes the TTS engine and sets its properties."""
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', 150)
            
            print("🎤 Voice Feedback System Initialized.")

        except Exception as e:
            self.engine = None
            print(f"Error initializing pyttsx3: {e}. Voice feedback will be disabled.")

    def say(self, text):
        """
        Speaks the given text aloud.
        """
        if self.engine:
            self.engine.say(text)
            self.engine.runAndWait()
        else:
            print(f"🎤 [DUMMY] FEEDBACK: {text}")

    def stop(self):
        """Stops the current speech playback."""
        if self.engine:
            self.engine.stop()

# Example usage for testing this module
if __name__ == '__main__':
    tts = VoiceFeedback()
    tts.say("Hello, I am NOVA guide. Testing, one, two, three.")
    tts.say("I can now speak using my legendary code.")