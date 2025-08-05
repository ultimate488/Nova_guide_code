# voice/recognizer.py
import vosk
import sounddevice as sd
import json
import sys
import numpy as np

# Change the path to the Indian English model
MODEL_PATH = "vosk-model-small-en-in-0.4"
SAMPLERATE = 16000

# Import the vocabulary from our config file
from config import VOSK_VOCABULARY

class VoiceRecognizer:
    def __init__(self, model_path=MODEL_PATH, samplerate=SAMPLERATE):
        if not vosk.os.path.exists(model_path):
            raise IOError("Vosk model not found. Please download and unzip it.")
        
        self.model = vosk.Model(model_path)
        self.samplerate = samplerate
        
        # Convert the list to a JSON grammar string
        grammar = json.dumps(VOSK_VOCABULARY)
        self.recognizer = vosk.KaldiRecognizer(self.model, self.samplerate, grammar)
        
        # Find and print the default input device
        try:
            device_info = sd.query_devices(None, 'input')
            device_list = sd.query_devices()
            self.device_index = 1 # Using the device ID for your headset
            print(f"🎙️ Using input device: {device_list[self.device_index]['name']} (ID: {self.device_index})")
        except sd.PortAudioError:
            print("Error: No audio input device found. Please check your microphone.")
            self.device_index = None

        print("🎙️ Voice Recognizer Initialized with fixed vocabulary.")

    def listen_for_command(self):
        print("Say a command...")
        
        try:
            with sd.InputStream(samplerate=self.samplerate, channels=1,
                                device=self.device_index, dtype='int16') as stream:
                while True:
                    data, overflowed = stream.read(8000)
                    audio_data_bytes = data.tobytes()

                    if self.recognizer.AcceptWaveform(audio_data_bytes):
                        result = json.loads(self.recognizer.Result())
                        command = result.get('text', '')
                        if command:
                            print(f"Heard: {command}")
                            self.recognizer.Reset()
                            return command
        except Exception as e:
            print(f"An error occurred in the audio stream: {e}", file=sys.stderr)
            return None