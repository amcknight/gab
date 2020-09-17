import pykka
import logging
from story.message import *

# Orchestrates the actions of the Cortex and Face
class Limbic(pykka.ThreadingActor):
    tags = None
    tag_confirmation_text = None
    tags_confirmed = False
    prompt_text = None
    prompt_path = None
    prompt_confirmed = False
    story_start_text = None
    story_start_path = None
    tag_audio_path = "story/input_audio/tag"
    yesno_audio_path = "story/input_audio/yesno"
    pages = []

    def on_receive(self, msg):
        logging.debug("Received: " + str(msg))
        if isinstance(msg, Go):
            self.go(msg)
        elif isinstance(msg, Prompt):
            self.prompt(msg)
        elif isinstance(msg, Story):
            self.story(msg)
        elif isinstance(msg, Heard):
            self.heard(msg)
        elif isinstance(msg, Said):
            self.said(msg)
        elif isinstance(msg, Composed):
            self.composed(msg)
        elif isinstance(msg, Interpreted):
            self.interpreted(msg)
        elif isinstance(msg, Confabulated):
            self.confabulated(msg)
        else:
            raise Exception("Unknown Limbic command: " + str(msg))

    def go(self, msg):
        face = pykka.ActorRegistry.get_by_class_name("Face")[0]
        face.tell(Say("intro", "story/res/intro.mp3"))
        face.tell(Hear("get_tags", 5))

    def prompt(self, msg):
        if self.prompt_path:
            self.pages.append(self.prompt_text)
            face = pykka.ActorRegistry.get_by_class_name("Face")[0]
            worker = pykka.ActorRegistry.get_by_class_name("Worker")[0]
            face.tell(Say("first_page", self.prompt_path))
            face.tell(Say("continue", "story/res/continue.mp3"))
            face.tell(Hear("prompt_confirmation", 2))
            worker.tell(Complete("page", "".join(self.pages), 200))
        else:
            self.actor_ref.tell(msg)

    def story(self, msg):
        if self.prompt_confirmed:
            face = pykka.ActorRegistry.get_by_class_name("Face")[0]
            face.tell(Say(msg.name, self.story_start_path))
        else:
            self.actor_ref.tell(msg)

    def heard(self, msg):
        worker = pykka.ActorRegistry.get_by_class_name("Worker")[0]
        if msg.named("get_tags"):
            worker.tell(SpeechToText("get_tags", msg.mp3_path))
        elif msg.named("tag_confirmation"):
            worker.tell(SpeechToText("tag_confirmation", msg.mp3_path))
        elif msg.named("prompt_confirmation"):
            worker.tell(SpeechToText("prompt_confirmation", msg.mp3_path))
        else:
            raise Exception("An unknown thing was heard! Creeeepy.")

    def said(self, msg):
        if msg.named("page"):
            worker = pykka.ActorRegistry.get_by_class_name("Worker")[0]
            worker.tell(Complete("page", "".join(self.pages), 200))
        else:
            pass

    def composed(self, msg):
        face = pykka.ActorRegistry.get_by_class_name("Face")[0]
        path = msg.mp3_path
        name = msg.name
        if msg.named("tag_confirmation"):
            if self.tags_confirmed:
                raise Exception("Trying to confirm tags after they've been confirmed")

            face.tell(Say(name, path))
            face.tell(Hear("tag_confirmation", 2))
        elif msg.named("story_prompt"):
            if self.prompt_path:
                raise Exception("Trying to generate story prompt audio when it already exists")

            self.prompt_path = path
        elif msg.named("first_page"):
            self.story_start_path = path
        elif msg.named("page"):
            face.tell(Say(name, path))
        else:
            raise Exception("Unknown text was converted into audio, named: " + name)

    def interpreted(self, msg):
        text = msg.text
        if msg.named("get_tags"):
            if not text or text == "":
                self.actor_ref.tell(Go("retry"))
            else:
                self.set_tags(text)
                worker = pykka.ActorRegistry.get_by_class_name("Worker")[0]
                worker.tell(TextToSpeech("tag_confirmation", self.tag_confirmation_text))
                worker.tell(Complete("tag_prompt", self.get_prompt(), 100))
        elif msg.named("tag_confirmation"):
            if self.tags_confirmed:
                raise Exception("Trying to confirm tags after they've been confirmed")

            if text == "Yes.":
                self.tags_confirmed = True
                self.actor_ref.tell(Prompt(""))
            elif text == "No.":
                raise Exception("You can't SAY no to ME!!")
            else:
                face = pykka.ActorRegistry.get_by_class_name("Face")[0]
                face.tell(Say("tag_confirmation", msg.mp3_path))
                face.tell(Hear("tag_confirmation", 2))
        elif msg.named("prompt_confirmation"):
            if self.prompt_confirmed:
                raise Exception("Trying to confirm prompt after it's been confirmed")

            if text == "Yes.":
                self.prompt_confirmed = True
                self.actor_ref.tell(Story(""))
            elif text == "No.":
                raise Exception("You can't SAY no to ME!!!")
            else:
                face = pykka.ActorRegistry.get_by_class_name("Face")[0]
                face.tell(Say("prompt_confirmation", msg.mp3_path))
                face.tell(Hear("prompt_confirmation", 2))
        else:
            raise Exception("Interpreted some unknown audio... voice in my head?")

    def confabulated(self, msg):
        text = msg.text
        worker = pykka.ActorRegistry.get_by_class_name("Worker")[0]
        if msg.named("tag_prompt"):
            if self.prompt_text:
                raise Exception("Trying to set prompt text when it already exists")

            self.prompt_text = text
            worker.tell(TextToSpeech("story_prompt", text))
        elif msg.named("first_page"):
            self.story_start_text = text
            worker.tell(TextToSpeech(msg.name, text))
        elif msg.named("page"):
            self.pages.append(text)
            worker.tell(TextToSpeech(msg.name, text))
        else:
            raise Exception("Unknown thing was confabulated. Am I ruminating?")

    def set_tags(self, text):
        if self.tags:
            raise Exception("Trying to set tags when already set")

        if text[-4:] == " and":
            text = text[-4:]
        self.tags = text.split(" and ")
        self.tag_confirmation_text = "Would you like to hear a story about " + self.andify(self.tags) + "?"

    def andify(self, ts):
        if len(ts) == 0:
            return ""
        if len(ts) == 1:
            return ts[0]
        tags2 = ts.copy()
        tags2[-1] = "and " + ts[-1]
        return ", ".join(tags2)

    def get_prompt(self):
        with open("story/res/tag2prompt.txt") as t2p_file:
            data = t2p_file.read()

        return data + "\n\n[tags] " + ", ".join(self.tags) + "\n[prompt]"
