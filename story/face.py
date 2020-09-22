import pykka
from functools import singledispatchmethod
from story import ear
from story import mouth
from story.message import *
from story.directory import limbic


# Does the sequential outward facing stuff
class Face(pykka.ThreadingActor):

    @singledispatchmethod
    def on_receive(self, msg):
        raise Exception("Unknown action sent to Face: " + str(msg))

    @on_receive.register(Say)
    def say(self, msg):
        mouth.say(msg.mp3_path)
        limbic().tell(Said(msg.name, msg.mp3_path))

    @on_receive.register(Hear)
    def hear(self, msg):
        mp3_path = ear.record("story/input_audio", msg.duration)
        limbic().tell(Heard(msg.name, mp3_path))
