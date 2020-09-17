import pykka
import os
from story import ear
from story import mouth


# Does the sequential outward facing stuff
class Face(pykka.ThreadingActor):
    def on_receive(self, message):
        print("Face: " + str(message))
        limbic = pykka.ActorRegistry.get_by_class_name("Limbic")[0]
        cmd, msg = message
        if cmd == "say":
            mouth.say(msg)
            limbic.tell(("said", msg))
        elif cmd == "hear":
            path, sec = msg
            mp3_path = ear.record(path, sec)
            limbic.tell(("heard", mp3_path))
