# config.py

# Your Picovoice AccessKey. Get this for free from https://console.picovoice.ai/
PICOVOICE_ACCESS_KEY = "GkFnWGAELI2/aW1vfOeSFyxcM1SH/PFn76n0dozrxvczmMe7uT/Hbw=="

# The path to your custom "NOVA" wake word model file for Windows.
# The file should be in the root directory of your project.
NOVA_WAKE_WORD_MODEL_PATH = "Nova-guide_en_windows_v3_0_0/Nova-guide_en_windows_v3_0_0.ppn"
# Recommended change: Increase sensitivity for a more responsive wake word
PICOVOICE_SENSITIVITY = 0.95


# Path to the Vosk speech recognition model
VOSK_MODEL_PATH = "vosk-model-small-en-in-0.4"

# A list of all the core commands the robot should listen for.
# Room names will be added dynamically.
VOSK_VOCABULARY = [
    "go to kitchen",
    "go to bathroom",
    "go outside",
    "go forward",
    "turn left",
    "turn right",
    "stop",
    "help",
    "return home",
    "exit",
    "yes",
    "no",
    "kitchen",
    "bathroom",
    "home",
    "outside",
]