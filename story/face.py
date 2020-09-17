import pykka
from story import ear
from story import mouth
from story.message import *


# Does the sequential outward facing stuff
class Face(pykka.ThreadingActor):
    def on_receive(self, msg):
        limbic = pykka.ActorRegistry.get_by_class_name("Limbic")[0]
        if isinstance(msg, Say):
            mouth.say(msg.mp3_path)
            limbic.tell(Said(msg.name, msg.mp3_path))
        elif isinstance(msg, Hear):
            mp3_path = ear.record("story/input_audio", msg.duration)
            limbic.tell(Heard(msg.name, mp3_path))
