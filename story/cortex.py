import re
import pykka
import openai
import logging
from functools import singledispatchmethod
from pykkachu.fleet import Fleet
from story import ear
from story import mouth
from story.message import *
from story.directory import limbic


# Does the tough long thinky stuff
class Cortex(Fleet):
    def __init__(self, num):
        super().__init__(Worker, num)


class Worker(pykka.ThreadingActor):
    @singledispatchmethod
    def on_receive(self, msg):
        raise Exception("Unknown command sent to worker: " + str(msg))

    @on_receive.register(SpeechToText)
    def s2t(self, msg):
        logging.info(type(msg).__name__ + ", " + msg.name)
        text = ear.speech_to_text(msg.mp3_path)
        limbic().tell(Interpreted(msg.name, msg.mp3_path, text))

    @on_receive.register(TextToSpeech)
    def t2s(self, msg):
        logging.info(type(msg).__name__ + ", " + msg.name)
        text = msg.text
        mp3_path = mouth.text_to_speech(text, "en-US", "story/input_audio")
        limbic().tell(Composed(msg.name, text, mp3_path))

    @on_receive.register(Complete)
    def complete(self, msg):
        logging.info(type(msg).__name__ + ", " + msg.name)
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
            logging.warning("Empty cleaned completion text. Raw completion length was " + str(len(text)))
            self.actor_ref.tell(Complete(msg.name, prompt, tokens))
        else:
            limbic().tell(Confabulated(msg.name, prompt, clean_text))
