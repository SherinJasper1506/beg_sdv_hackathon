
import subprocess
import sys

def text_to_speech(text):
    shell_cmd_espeak_open = subprocess.Popen(f"espeak '{text}'", shell=True)
    shell_cmd_espeak_return = shell_cmd_espeak_open.wait()
    if (shell_cmd_espeak_return):
        print("\nERROR: failure in processing Shell Command")

text_to_speech("Hello, welcome to the world of text-to-speech synthesis!")

print("Text successfully converted to speech using eSpeak.")