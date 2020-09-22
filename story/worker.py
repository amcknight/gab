import re

import pykka
import openai
from story import ear
from story import mouth
from functools import singledispatchmethod

from story.message import *


# Does the tough long thinky stuff and so needs to be a fleet of concurrent workers
class Worker(pykka.ThreadingActor):
    @singledispatchmethod
    def on_receive(self, msg):
        raise Exception("Unknown command sent to worker: " + str(msg))

    @on_receive(SpeechToText)
    def s2t(self, msg):
        text = ear.speech_to_text(msg.mp3_path)
        limbic = pykka.ActorRegistry.get_by_class_name("Limbic")[0]
        limbic.tell(Interpreted(msg.name, msg.mp3_path, text))

    @on_receive(TextToSpeech)
    def t2s(self, msg):
        text = msg.text
        mp3_path = mouth.text_to_speech(text, "en-US", "story/input_audio")
        limbic = pykka.ActorRegistry.get_by_class_name("Limbic")[0]
        limbic.tell(Composed(msg.name, text, mp3_path))

    @on_receive(Complete)
    def complete(self, msg):
        prompt = msg.prompt
        tokens = msg.tokens
        response = openai.Completion.create(engine="davinci", prompt=prompt, max_tokens=tokens)
        text = response.choices[0].text.strip()
        ending = re.split("\.|\n|!|\?", text)[-1]
        truncated_text = text[:-len(ending)].strip()
        clean_text = truncated_text.split("-----")[0]
        clean_text = clean_text.split("[tags]")[0]
        clean_text = clean_text.split("[prompt]")[0]
        clean_text.strip()
        if clean_text == "":
            print("Empty cleaned completion text. Raw completion length was " + str(len(text)))
            self.actor_ref.tell(Complete(msg.name, prompt, tokens))
        else:
            limbic = pykka.ActorRegistry.get_by_class_name("Limbic")[0]
            limbic.tell(Confabulated(msg.name, prompt, clean_text))