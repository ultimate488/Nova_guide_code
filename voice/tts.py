# voice/tts.py

import multiprocessing
import queue
from gtts import gTTS
from playsound import playsound
import tempfile
import os

class AudioProcess(multiprocessing.Process):
    """
    A dedicated, isolated process for handling all text-to-speech requests.

    This "genius" version uses a robust two-step pipeline:
    1. gTTS: Converts text to a high-quality MP3 file.
    2. playsound: Plays the generated audio file.
    This architecture is extremely reliable and avoids the common pitfalls of
    using complex TTS engines directly inside a child process.
    """
    def __init__(self, audio_queue):
        super().__init__()
        self.audio_queue = audio_queue
        # Make this a daemon process so it exits when the main program does
        self.daemon = True

    def run(self):
        """The main loop for the audio server process."""
        print("🎤 Legendary Audio Server Process started.")
        while True:
            try:
                # This call will block efficiently, waiting for a message.
                text = self.audio_queue.get()

                # A 'None' message is our signal to shut down gracefully.
                if text is None:
                    print("🎤 Audio Server received shutdown signal.")
                    break

                print(f"AudioProcess speaking: '{text}'")

                # 1. Generate the speech and save it to a temporary file
                tts = gTTS(text=text, lang='en', tld='co.in') # 'co.in' for Indian English accent
                
                # Using a temporary file is the most compatible way across OSes
                with tempfile.NamedTemporaryFile(delete=True, suffix='.mp3') as fp:
                    temp_filename = fp.name
                
                tts.save(temp_filename)
                
                # 2. Play the generated audio file
                playsound(temp_filename)
                
                # 3. Clean up the temporary file
                os.remove(temp_filename)


            except queue.Empty:
                continue # Should not happen with blocking .get()
            except Exception as e:
                # Catch potential gTTS/playsound errors (e.g., no internet connection)
                print(f"Error in AudioProcess: {e}")

        print("🎤 Audio Server Process shutting down.")