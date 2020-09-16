import pykka
from story import ear
from story import mouth

# Does the tough long thinky stuff and so needs to be a fleet of concurrent workers
class Worker(pykka.ThreadingActor):
    def on_receive(self, message):
        cmd, msg = message
        if cmd == "s2t":
            print("Worker s2t " + msg)
            text = ear.speech_to_text(msg)
            limbic = pykka.ActorRegistry.get_by_class_name("Limbic")[0]
            limbic.tell(("interpreted", (msg, text)))
        elif cmd == "t2s":
            mp3 = mouth.text_to_speech(msg, "en-US", "story/input_audio")
            limbic = pykka.ActorRegistry.get_by_class_name("Limbic")[0]
            limbic.tell(("composed", (msg, mp3)))
