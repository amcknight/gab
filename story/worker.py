import pykka
import openai
from story import ear
from story import mouth

# Does the tough long thinky stuff and so needs to be a fleet of concurrent workers
class Worker(pykka.ThreadingActor):
    def on_receive(self, message):
        cmd, msg = message
        if cmd == "s2t":
            self.s2t(msg)
        elif cmd == "t2s":
            self.t2s(msg)

    def s2t(self, mp3_path):
        print("Worker s2t " + mp3_path)
        text = ear.speech_to_text(mp3_path)
        limbic = pykka.ActorRegistry.get_by_class_name("Limbic")[0]
        limbic.tell(("interpreted", (mp3_path, text)))

    def t2s(self, text):
        print("Worker t2s " + text)
        mp3 = mouth.text_to_speech(text, "en-US", "story/input_audio")
        limbic = pykka.ActorRegistry.get_by_class_name("Limbic")[0]
        limbic.tell(("composed", (text, mp3)))

    def complete(prompt, tokens):
        response = openai.Completion.create(engine="davinci", prompt=prompt, max_tokens=tokens)
        return response.choices[0].text
