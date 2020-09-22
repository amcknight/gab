import pykka
from functools import singledispatchmethod
from story import ear
from story import mouth
from story.message import *


# Does the sequential outward facing stuff
class Face(pykka.ThreadingActor):

    @singledispatchmethod
    def on_receive(self, msg):
        raise Exception("Unknown action sent to Face: " + str(msg))

    @on_receive(Say)
    def say(self, msg):
        limbic = pykka.ActorRegistry.get_by_class_name("Limbic")[0]
        mouth.say(msg.mp3_path)
        limbic.tell(Said(msg.name, msg.mp3_path))

    @on_receive(Hear)
    def hear(self, msg):
        limbic = pykka.ActorRegistry.get_by_class_name("Limbic")[0]
        mp3_path = ear.record("story/input_audio", msg.duration)
        limbic.tell(Heard(msg.name, mp3_path))
