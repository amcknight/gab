import os
import secrets

from google.cloud import texttospeech

client = texttospeech.TextToSpeechClient()

def say(mp3):
    os.system("afplay " + mp3)

def text_to_speech(text, lang_code, path):
    response = client.synthesize_speech(
        input=texttospeech.SynthesisInput(
            text=text
        ),
        voice=texttospeech.VoiceSelectionParams(
            language_code=lang_code,
            ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
        ),
        audio_config=texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )
    )

    if not os.path.exists(path):
        os.makedirs(path)

    out_file = path + "/" + secrets.token_hex(6) + ".mp3"
    with open(out_file, "wb") as out:
        out.write(response.audio_content)
    return out_file
