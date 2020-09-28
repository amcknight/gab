import logging

import pykka
from functools import singledispatchmethod

from story.decorators import *
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

    @on()
    def unknown(self, event, state):
        raise Exception("Unknown Limbic command: " + str(type(event)) + ", " + event.name + ", " + state.name)

    @on(Go, state=have_none)
    def go_without_tags(self, _event):
        face().tell(Say("intro", "story/res/intro.mp3"))
        face().tell(Hear("get_tags", 5))

    @on(Go)
    def go_with_tags(self, event):
        raise Exception("Trying to Go when already going")

    @on(Prompt)
    def prompt(self, event):
        if self.prompt_path:
            self.pages.append(self.prompt_text)
            face().tell(Say("first_page", self.prompt_path))
            face().tell(Say("continue", "story/res/continue.mp3"))
            face().tell(Hear("prompt_confirmation", 2))
            cortex().tell(Complete("first_page", "".join(self.pages), 200))
        else:
            self.actor_ref.tell(event)

    @on(Story)
    def story(self, event):
        if self.story_start_path:
            face().tell(Say(event.name, self.story_start_path))
        else:
            self.actor_ref.tell(event)

    @on(Heard, "get_tags")
    def heard_get_tags(self, event):
        cortex().tell(SpeechToText("get_tags", event.mp3_path))

    @on(Heard, "tag_confirmation")
    def heard_tag_confirmation(self, event):
        cortex().tell(SpeechToText("tag_confirmation", event.mp3_path))

    @on(Heard, "prompt_confirmation")
    def heard_prompt_confirmation(self, event):
        cortex().tell(SpeechToText("prompt_confirmation", event.mp3_path))

    @on(Heard)
    def heard(self, _event):
        raise Exception("An unknown thing was heard! Creeeepy.")

    @on(Said, "first_page")
    def said_first_page(self, _event):
        cortex().tell(Complete("page", "".join(self.pages), 200))

    @on(Said, "page")
    def said_first_page(self, _event):
        cortex().tell(Complete("page", "".join(self.pages), 200))

    @on(Said)
    def said(self, _event):
        pass

    @on(Composed, "tag_confirmation", have_tags)
    def composed_tag_confirm_again(self, _event):
        raise Exception("Trying to confirm tags after they've been confirmed")

    @on(Composed, "tag_confirmation")
    def composed_tag_confirm(self, event):
        path = event.mp3_path
        name = event.name
        self.tag_confirmation_path = path
        face().tell(Say(name, path))
        face().tell(Hear(name, 2))

    @on(Composed, "story_prompt")
    def composed_story_prompt(self, event):
        if self.prompt_path:
            raise Exception("Trying to generate story prompt audio when it already exists")

        self.prompt_path = event.mp3_path

    @on(Composed, "first_page")
    def composed_first_page(self, event):
        self.story_start_path = event.mp3_path

    @on(Composed, "page", storying)
    def composed_page(self, event):
        face().tell(Say(event.name, event.mp3_path))

    @on(Composed)
    def composed(self, event):
        raise Exception("Unknown text was converted into audio, named: " + event.name)

    @on(Interpreted, "get_tags")
    def interpreted_tags(self, event):
        text = event.text
        if not text or text == "":
            self.actor_ref.tell(Go("retry"))
        else:
            self.set_tags(text)
            cortex().tell(TextToSpeech("tag_confirmation", self.tag_confirmation_text))
            cortex().tell(Complete("tag_prompt", self.get_prompt(), 100))

    @on(Interpreted, "tag_confirmation", have_tags)
    def interpreted_tag_confirm_again(self, _event):
        raise Exception("Trying to confirm tags after they've been confirmed")

    @on(Interpreted, "tag_confirmation")
    def interpreted_tag_confirm(self, event):
        text = event.text
        if text == "Yes.":
            self.sm.dispatch(Event('have_tags'))
            self.actor_ref.tell(Prompt(""))
        elif text == "No.":
            raise Exception("You can't SAY no to ME!!")
        else:
            face().tell(Say("tag_confirmation", self.tag_confirmation_path))
            face().tell(Hear("tag_confirmation", 2))

    @on(Interpreted, "prompt_confirmation", have_prompt)
    def interpreted_prompt_confirm_again(self, _event):
        raise Exception("Trying to confirm prompt after it's been confirmed")

    @on(Interpreted, "prompt_confirmation")
    def interpreted_prompt_confirm(self, event):
        text = event.text
        if text == "Yes.":
            self.sm.dispatch(Event('have_prompt'))
            self.actor_ref.tell(Story(""))
        elif text == "No.":
            raise Exception("You can't SAY no to ME!!!")
        else:
            face().tell(Say("prompt_confirmation", "story/res/continue.mp3"))
            face().tell(Hear("prompt_confirmation", 2))


    @on(Interpreted)
    def interpreted(self, event):
        raise Exception("Interpreted some unknown audio... voice in my head?")


    @on(Confabulated, "tag_prompt", prompt_text)
    def confabulated_tag_prompt_again(self, event):
        raise Exception("Trying to set prompt text when it already exists")

    @on(Confabulated, "tag_prompt")
    def confabulated_tag_prompt(self, event):
        self.prompt_text = event.text
        cortex().tell(TextToSpeech("story_prompt", event.text))

    @on(Confabulated, "first_page")
    def confabulated_first_page(self, event):
        self.story_start_text = event.text
        cortex().tell(TextToSpeech(event.name, event.text))

    @on(Confabulated, "page")
    def confabulated_page(self, event):
        self.pages.append(event.text)
        cortex().tell(TextToSpeech(event.name, event.text))

    @on(Confabulated)
    def confabulated(self, _event):
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
