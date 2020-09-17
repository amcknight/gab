import re

import pykka
import openai
from story import ear
from story import mouth


# Does the tough long thinky stuff and so needs to be a fleet of concurrent workers
class Worker(pykka.ThreadingActor):
    def on_receive(self, message):
        cmd, msg = message
        if cmd == "s2t":
            id, mp3_path = msg
            self.s2t(id, mp3_path)
        elif cmd == "t2s":
            id, text = msg
            self.t2s(id, text)
        elif cmd == "complete":
            id, text, tokens = msg
            self.complete(id, text, tokens)
        else:
            raise Exception("Unknown command sent to worker: " + cmd)

    def s2t(self, id, mp3_path):
        text = ear.speech_to_text(mp3_path)
        limbic = pykka.ActorRegistry.get_by_class_name("Limbic")[0]
        limbic.tell(("interpreted", (id, mp3_path, text)))

    def t2s(self, id, text):
        mp3_path = mouth.text_to_speech(text, "en-US", "story/input_audio")
        limbic = pykka.ActorRegistry.get_by_class_name("Limbic")[0]
        limbic.tell(("composed", (id, text, mp3_path)))

    def complete(self, id, prompt, tokens):
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
            self.actor_ref.tell(("complete", (id, prompt, tokens)))
        else:
            limbic = pykka.ActorRegistry.get_by_class_name("Limbic")[0]
            limbic.tell(("confabulated", (id, prompt, clean_text)))