import logging

import pykka
from functools import singledispatchmethod
from story.message import *
from story.directory import *
from pysm import State, StateMachine, Event


# Orchestrates the actions of the Cortex and Face
class Limbic(pykka.ThreadingActor):
    sm = StateMachine('sm')
    have_none = State('have_none')
    have_tags = State('have_tags')
    have_prompt = State('have_prompt')
    storying = State('storying')
    sm.add_state(have_none, initial=True)
    sm.add_state(have_tags)
    sm.add_state(have_prompt)
    sm.add_state(storying)
    sm.add_transition(have_none, have_tags, events=['have_tags'])
    sm.add_transition(have_tags, have_prompt, events=['have_prompt'])
    sm.add_transition(have_prompt, storying, events=['storying'])
    sm.initialize()

    tags = None
    tag_confirmation_text = None
    tag_confirmation_path = None
    prompt_text = None
    prompt_path = None
    story_start_text = None
    story_start_path = None
    tag_audio_path = "story/input_audio/tag"
    yesno_audio_path = "story/input_audio/yesno"
    pages = []

    @singledispatchmethod
    def on_receive(self, msg):
        raise Exception("Unknown Limbic command: " + str(msg))

    @on_receive.register(Go)
    def go(self, msg):
        self.trace(msg)
        if self.sm.state == self.have_none:
            face().tell(Say("intro", "story/res/intro.mp3"))
            face().tell(Hear("get_tags", 5))
        else:
            raise Exception("Trying to Go when not on have_none state")

    @on_receive.register(Prompt)
    def prompt(self, msg):
        self.trace(msg)
        if self.prompt_path:
            self.pages.append(self.prompt_text)
            face().tell(Say("first_page", self.prompt_path))
            face().tell(Say("continue", "story/res/continue.mp3"))
            face().tell(Hear("prompt_confirmation", 2))
            cortex().tell(Complete("first_page", "".join(self.pages), 200))
        else:
            self.actor_ref.tell(msg)

    @on_receive.register(Story)
    def story(self, msg):
        self.trace(msg)
        if self.story_start_path:
            face().tell(Say(msg.name, self.story_start_path))
        else:
            self.actor_ref.tell(msg)

    @on_receive.register(Heard)
    def heard(self, msg):
        self.trace(msg)
        if msg.named("get_tags"):
            cortex().tell(SpeechToText("get_tags", msg.mp3_path))
        elif msg.named("tag_confirmation"):
            cortex().tell(SpeechToText("tag_confirmation", msg.mp3_path))
        elif msg.named("prompt_confirmation"):
            cortex().tell(SpeechToText("prompt_confirmation", msg.mp3_path))
        else:
            raise Exception("An unknown thing was heard! Creeeepy.")

    @on_receive.register(Said)
    def said(self, msg):
        self.trace(msg)
        if msg.named("first_page"):
            cortex().tell(Complete("page", "".join(self.pages), 200))
        elif msg.named("page"):
            cortex().tell(Complete("page", "".join(self.pages), 200))
        else:
            pass

    @on_receive.register(Composed)
    def composed(self, msg):
        self.trace(msg)
        path = msg.mp3_path
        name = msg.name
        if msg.named("tag_confirmation"):
            if self.sm.state == self.have_tags:
                raise Exception("Trying to confirm tags after they've been confirmed")

            self.tag_confirmation_path = path
            face().tell(Say(name, path))
            face().tell(Hear(name, 2))
        elif msg.named("story_prompt"):
            if self.prompt_path:
                raise Exception("Trying to generate story prompt audio when it already exists")

            self.prompt_path = path
        elif msg.named("first_page"):
            self.story_start_path = path
        elif msg.named("page"):
            if self.sm.state == self.storying:
                face().tell(Say(name, path))
        else:
            raise Exception("Unknown text was converted into audio, named: " + name)

    @on_receive.register(Interpreted)
    def interpreted(self, msg):
        self.trace(msg)
        text = msg.text
        if msg.named("get_tags"):
            if not text or text == "":
                self.actor_ref.tell(Go("retry"))
            else:
                self.set_tags(text)
                cortex().tell(TextToSpeech("tag_confirmation", self.tag_confirmation_text))
                cortex().tell(Complete("tag_prompt", self.get_prompt(), 100))
        elif msg.named("tag_confirmation"):
            if self.sm.state == self.have_tags:
                raise Exception("Trying to confirm tags after they've been confirmed")

            if text == "Yes.":
                self.sm.dispatch(Event('have_tags'))
                self.actor_ref.tell(Prompt(""))
            elif text == "No.":
                raise Exception("You can't SAY no to ME!!")
            else:
                face().tell(Say("tag_confirmation", self.tag_confirmation_path))
                face().tell(Hear("tag_confirmation", 2))
        elif msg.named("prompt_confirmation"):
            if self.sm.state == self.have_prompt:
                raise Exception("Trying to confirm prompt after it's been confirmed")

            if text == "Yes.":
                self.sm.dispatch(Event('have_prompt'))
                self.actor_ref.tell(Story(""))
            elif text == "No.":
                raise Exception("You can't SAY no to ME!!!")
            else:
                face().tell(Say("prompt_confirmation", "story/res/continue.mp3"))
                face().tell(Hear("prompt_confirmation", 2))
        else:
            raise Exception("Interpreted some unknown audio... voice in my head?")

    @on_receive.register(Confabulated)
    def confabulated(self, msg):
        self.trace(msg)
        text = msg.text
        name = msg.name
        if msg.named("tag_prompt"):
            if self.prompt_text:
                raise Exception("Trying to set prompt text when it already exists")

            self.prompt_text = text
            cortex().tell(TextToSpeech("story_prompt", text))
        elif msg.named("first_page"):
            self.story_start_text = text
            cortex().tell(TextToSpeech(name, text))
        elif msg.named("page"):
            self.pages.append(text)
            cortex().tell(TextToSpeech(name, text))
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

    def trace(self, msg):
        logging.warning(type(msg).__name__ + ", " + msg.name + ", " + self.sm.state.name)
