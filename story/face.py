import pykka
import os
from story import ear
from story import mouth


# Does the sequential outward facing stuff
class Face(pykka.ThreadingActor):
    def on_receive(self, message):
        limbic = pykka.ActorRegistry.get_by_class_name("Limbic")[0]
        cmd, msg = message
        if cmd == "say":
            id, mp3_path = msg
            mouth.say(mp3_path)
            limbic.tell(("said", (id, mp3_path)))
        elif cmd == "hear":
            id, sec = msg
            mp3_path = ear.record("story/input_audio", sec)
            limbic.tell(("heard", (id, mp3_path)))
