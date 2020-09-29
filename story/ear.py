import sounddevice as sd
import soundfile as sf
import pydub
import os
import io
import secrets
from google.cloud import speech_v1p1beta1
from google.cloud.speech_v1p1beta1 import enums
from google.cloud.speech_v1p1beta1 import types

sd.default.samplerate = 44100
sd.default.channels = 2

client = speech_v1p1beta1.SpeechClient()


def record(path, duration):
    name = path + "/" + secrets.token_hex(6)
    wav_name = name + ".wav"
    mp3_name = name + ".mp3"
    rate = 44100
    print("[Start]")
    data = sd.rec(duration * rate, blocking=True)
    print("[Stop]")
    sf.write(wav_name, data, sd.default.samplerate)
    sound = pydub.AudioSegment.from_wav(wav_name)
    sound.export(mp3_name, format="mp3")
    os.remove(wav_name)
    return mp3_name


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
