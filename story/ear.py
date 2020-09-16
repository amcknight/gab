import sounddevice as sd
import soundfile as sf
import pydub
import os
import io
from google.cloud import speech_v1p1beta1
from google.cloud.speech_v1p1beta1 import enums
from google.cloud.speech_v1p1beta1 import types

sd.default.samplerate=44100
sd.default.channels=2

client = speech_v1p1beta1.SpeechClient()

def record(name, duration):
    rate = 44100
    print("* recording")
    data = sd.rec(duration*rate, blocking=True)
    print("* done recording")
    sf.write(name + ".wav", data, sd.default.samplerate)
    sound = pydub.AudioSegment.from_wav(name + ".wav")
    sound.export(name + ".mp3", format="mp3")
    os.remove(name + ".wav")
    return name + ".mp3"

def speech_to_text(mp3):
    config = types.RecognitionConfig(
        encoding=enums.RecognitionConfig.AudioEncoding.MP3,
        sample_rate_hertz=sd.default.samplerate,
        language_code='en-US',
        enable_automatic_punctuation=True)
    with io.open(mp3, "rb") as f:
        content = f.read()
    audio = {"content": content}

    results = client.recognize(config, audio).results
    if len(results) < 1:
        return None
    result = results[0]
    text = result.alternatives[0].transcript
    return text