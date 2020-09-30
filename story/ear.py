import sounddevice as sd
import soundfile as sf
import pydub
import os
import io
import secrets
from google.cloud import speech_v1p1beta1 as speechtotext

sd.default.samplerate = 44100
sd.default.channels = 2

client = speechtotext.SpeechClient()


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
    config = speechtotext.RecognitionConfig({
        'encoding': speechtotext.RecognitionConfig.AudioEncoding.MP3,
        'sample_rate_hertz': sd.default.samplerate,
        'language_code': 'en-US',
        'enable_automatic_punctuation': True
    })
    with io.open(mp3, "rb") as f:
        content = f.read()
    audio = speechtotext.RecognitionAudio({"content": content})

    results = client.recognize(config=config, audio=audio).results
    if len(results) < 1:
        return None
    result = results[0]
    text = result.alternatives[0].transcript
    return text
