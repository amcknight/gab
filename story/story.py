#!/usr/bin/env python3

import re
import os
import openai
import io
import pyaudio
import wave
import pydub
import asyncio
from playsound import playsound
from google.cloud import texttospeech
from google.cloud import speech_v1p1beta1
from google.cloud.speech_v1p1beta1 import enums
from google.cloud.speech_v1p1beta1 import types

t2s_client = texttospeech.TextToSpeechClient()
s2t_client = speech_v1p1beta1.SpeechClient()

CHUNK = 8192
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

p = pyaudio.PyAudio()


async def play(file):
    print("Playing " + file)
    playsound(file)
    print("Stopped " + file)


async def speech_to_text(path):
    print("SPEECH to TEXT on " + path + " STARTED")
    config = types.RecognitionConfig(
        encoding=enums.RecognitionConfig.AudioEncoding.MP3,
        sample_rate_hertz=RATE,
        language_code='en-US',
        enable_automatic_punctuation=True)
    with io.open(path, "rb") as f:
        content = f.read()
    audio = {"content": content}

    results = s2t_client.recognize(config, audio).results
    if len(results) < 1:
        return None
    result = results[0]
    text = result.alternatives[0].transcript
    print("SPEECH to TEXT on " + path + "ENDED")
    return text


async def text_to_speech(text, voice):
    return t2s_client.synthesize_speech(
        input=texttospeech.SynthesisInput(
            text=text
        ),
        voice=texttospeech.VoiceSelectionParams(
            language_code=voice,
            ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
        ),
        audio_config=texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )
    )


async def speak(text, voice, path):
    print("SPEAK " + text + " to " + path + " STARTED")
    response = await text_to_speech(text, voice)
    # if not os.path.exists(folder):
    #     os.makedirs(folder)

    with open(path, "wb") as out:
        out.write(response.audio_content)

    print("SPEAK " + text + " to " + path + "ENDED")
    return asyncio.create_task(play(path))


def record(name, seconds):
    wf = wave.open(name + ".wav", 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)

    print("* recording")

    frames = []

    for i in range(0, int(RATE / CHUNK * seconds)):
        data = stream.read(CHUNK)
        frames.append(data)

    print("* done recording")

    stream.stop_stream()
    stream.close()
    wf.writeframes(b''.join(frames))
    wf.close()

    sound = pydub.AudioSegment.from_wav(name + ".wav")
    sound.export(name + ".mp3", format="mp3")
    os.remove(name + ".wav")


def complete(prompt, tokens):
    response = openai.Completion.create(engine="davinci", prompt=prompt, max_tokens=tokens)
    return response.choices[0].text


async def complete_sentences(prompt, tokens):
    response = complete(prompt, tokens)
    ending = re.split("\.|\n|!|\?", response)[-1]
    return response[:-len(ending)]


def andify(tags):
    if len(tags) == 0:
        return ""
    if len(tags) == 1:
        return tags[0]
    tags2 = tags.copy()
    tags2[-1] = "and " + tags[-1]
    return ", ".join(tags2)


def get_prompt(tags):
    with open("story/res/tag2prompt.txt") as t2p_file:
        data = t2p_file.read()

    return data + "\n\n[tags] " + ", ".join(tags) + "\n[prompt]"


async def ask_yesno(question):
    while True:
        await speak(question, "en-US", "question.mp3")
        record("story/res/yesno", 3)
        raw = await speech_to_text("story/res/yesno.mp3")
        if raw == "Yes.":
            return True
        elif raw == "No.":
            return False


def get_tags(text):
    if text[-4:] == " and":
        text = text[-4:]
    tags = text.split(" and ")
    return tags


async def stuff():
    print("TASK EXECUTED")


async def storytime():
    asyncio.create_task(stuff())
    # speak("Welcome to story time! Name some things to include in your story:", "en-US", "story/res/intro.mp3")
    await play("story/res/intro.mp3")
    record("story/input_audio", 5)
    tags_text = await speech_to_text("story/input_audio.mp3")
    tags = get_tags(tags_text)
    confirm_tags_task = speak("This is a story about " + andify(tags), "en-US", "story/tags.mp3")
    t2p = get_prompt(tags)
    prompt = await complete_sentences(t2p, 100)
    await confirm_tags_task
    await speak(prompt, "en-GB", "story/prompt.mp3")
    go = await ask_yesno("Would you like to continue this story?")

    more_story = prompt
    while go:
        prev_story_part_task = speak(more_story, "en-GB", "story/story.mp3")
        more_story = await complete_sentences(prompt, 200)
        await prev_story_part_task
    await speak("Goodbye, and have a wonderful night", "en-US", "story/res/goodbye.mp3")

