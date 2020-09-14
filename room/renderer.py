import random
import os
import secrets
from playsound import playsound
from google.cloud import texttospeech

conversation_code = secrets.token_hex(4)
client = texttospeech.TextToSpeechClient()
mp3_folder = "/Users/amc/git/gab/" + conversation_code
voices = [
    "en-US-Standard-A", "en-US-Standard-B", "en-US-Standard-C", "en-US-Standard-D",
    "en-IN-Standard-A", "en-IN-Standard-B", "en-IN-Standard-C", "en-IN-Standard-D",
    "en-AU-Standard-A", "en-AU-Standard-B", "en-AU-Standard-C", "en-AU-Standard-D",
    "en-UK-Standard-A", "en-UK-Standard-B", "en-UK-Standard-C", "en-UK-Standard-D"
]
line_num = 0


def go(action, person):
    return "[" + action + ": " + person + "]"


def enter(person, cast):
    cast[person] = {'voice': random.choice(voices)}
    return go("ENTER", person)


def exit(person, cast):
    del cast[person]
    return go("EXIT", person)


def say(person, words):
    return person + "> " + words


def prefix_line(line):
    # No prefix
    return line


def format(lines):
    return "\n".join(map(prefix_line, lines))


def text_to_speech(text, voice):
    global client
    return client.synthesize_speech(
        input=texttospeech.SynthesisInput(
            text=text
        ),
        voice=texttospeech.VoiceSelectionParams(
            language_code="-".join(voice.split('-')[0:2]),
            ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
        ),
        audio_config=texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )
    )


def speak(text, voice):
    global line_num
    response = text_to_speech(text, voice)
    if not os.path.exists(mp3_folder):
        os.makedirs(mp3_folder)

    line_num += 1
    out_path = mp3_folder + "/" + str(line_num) + ".mp3"
    with open(out_path, "wb") as out:
        # Write the response to the output file.
        out.write(response.audio_content)

    playsound(out_path)
