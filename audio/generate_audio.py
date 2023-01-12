import os
import subprocess

try:
    from gtts import gTTS
except:
    print("ERROR: Please install the gtts pip package!")
    exit(1)

audios = [
    ["mac_success", "MAC success"],
    ["mac_failure", "MAC failure"],
    ["name_success", "Name success"],
    ["name_failure", "Name failure"],
]

tempo = 1.8


def generate_audios(out_dir="."):
    for audio in audios:
        tts = gTTS(audio[1], lang="en")
        tts.save(f"{out_dir}/{audio[0]}.mp3")
        # Convert to ogg with ffmpeg and change tempo
        subprocess.run([
            "ffmpeg", "-i", f"{out_dir}/{audio[0]}.mp3",
            "-filter:a", f"atempo={tempo}",
            f"{out_dir}/{audio[0]}.ogg",
        ])
        os.remove(f"{out_dir}/{audio[0]}.mp3")


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.realpath(__file__))
    generate_audios(script_dir)
