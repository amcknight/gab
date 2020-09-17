import pykka
import openai
from story import ear
from story import mouth

# Does the tough long thinky stuff and so needs to be a fleet of concurrent workers
class Worker(pykka.ThreadingActor):
    def on_receive(self, message):
        print("Worker: " + str(message))
        cmd, msg = message
        if cmd == "s2t":
            self.s2t(msg)
        elif cmd == "t2s":
            self.t2s(msg)
        elif cmd == "complete":
            id, text, tokens = msg
            self.complete(id, text, tokens)
        else:
            raise Exception("Unknown command sent to worker: " + cmd)

    def s2t(self, mp3_path):
        text = ear.speech_to_text(mp3_path)
        limbic = pykka.ActorRegistry.get_by_class_name("Limbic")[0]
        limbic.tell(("interpreted", (mp3_path, text)))

    def t2s(self, text):
        mp3_path = mouth.text_to_speech(text, "en-US", "story/input_audio")
        limbic = pykka.ActorRegistry.get_by_class_name("Limbic")[0]
        limbic.tell(("composed", (text, mp3_path)))

    def complete(self, id, prompt, tokens):
        response = openai.Completion.create(engine="davinci", prompt=prompt, max_tokens=tokens)
        limbic = pykka.ActorRegistry.get_by_class_name("Limbic")[0]
        limbic.tell(("confabulated", (id, prompt, response.choices[0].text)))
