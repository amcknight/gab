import pykka

"""Orchestrates the actions of the Cortex and Face"""
class Limbic(pykka.ThreadingActor):

    tags = None
    tag_confirmation_text = None
    tags_confirmed = False
    prompt = None
    story_part = None
    tag_audio_path = "story/tag_audio"

    def on_receive(self, message):
        print("Limbic: " + str(message))
        cmd, msg = message
        if cmd == "go":
            self.go()
        elif cmd == "heard":
            self.heard(msg)
        elif cmd == "said":
            self.said(msg)
        elif cmd == "composed":
            text, mp3_path = msg
            self.composed(text, mp3_path)
        elif cmd == "interpreted":
            mp3_path, text = msg
            self.interpreted(mp3_path, text)
        elif cmd == "confabulated":
            prompt, text = msg
            self.confabulated(prompt, text)
        else:
            raise("Unknown Limbic command: " + cmd)

    def go(self):
        face = pykka.ActorRegistry.get_by_class_name("Face")[0]
        face.tell(("say", "story/res/intro.mp3"))
        face.tell(("hear", (self.tag_audio_path, 5)))

    def heard(self, mp3_path):
        worker = pykka.ActorRegistry.get_by_class_name("Worker")[0]
        if mp3_path == self.tag_audio_path + ".mp3":
            worker.tell(("s2t", mp3_path))
        else:
            print("HEARD!!!")

    def said(self, mp3_path):
        print("SAID!!!")

    def composed(self, text, mp3_path):
        if text == self.tag_confirmation_text:
            if self.tags_confirmed:
                raise Exception("Trying to confirm tags after they've been confirmed")
            else:
                face = pykka.ActorRegistry.get_by_class_name("Face")[0]
                face.tell(("say", mp3_path))
        else:
            print("COMPOSED!!!")

    def interpreted(self, mp3_path, text):
        if mp3_path == self.tag_audio_path + ".mp3":
            self.set_tags(text)
            self.tag_confirmation_text = "Would you like to hear a story about " + self.andify()
            worker = pykka.ActorRegistry.get_by_class_name("Worker")[0]
            worker.tell(("t2s", self.tag_confirmation_text))
        else:
            print("INTERPRETED!!!")

    def confabulated(self, prompt, text):
        print("CONFABULATED!!!")

    def set_tags(self, text):
        if self.tags:
            raise Exception("Trying to set tags when already set")

        if text[-4:] == " and":
            text = text[-4:]
        self.tags = text.split(" and ")

    def andify(self):
        ts = self.tags
        if len(ts) == 0:
            return ""
        if len(ts) == 1:
            return ts[0]
        tags2 = ts.copy()
        tags2[-1] = "and " + ts[-1]
        return ", ".join(tags2)