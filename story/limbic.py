import pykka

"""Orchestrates the actions of the Cortex and Face"""
class Limbic(pykka.ThreadingActor):

    tags = None
    prompt = None
    story_part = None
    tag_audio_path = "story/tag_audio"

    def on_receive(self, message):
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
        print("go")
        face = pykka.ActorRegistry.get_by_class_name("Face")[0]
        face.tell(("say", "story/res/intro.mp3"))
        face.tell(("hear", (self.tag_audio_path, 5)))

    def heard(self, mp3_path):
        print("heard " + mp3_path)
        if mp3_path == self.tag_audio_path + ".mp3":
            print("NEED TO PROCESS TAGS HERE")
        worker = pykka.ActorRegistry.get_by_class_name("Worker")[0]
        worker.tell(("s2t", mp3_path))

    def said(self, mp3_path):
        print("said " + mp3_path)

    def composed(self, text, mp3_path):
        print(text + " --> " + mp3_path)

    def interpreted(self, mp3_path, text):
        print(mp3_path + " --> " + text)

    def confabulated(self, prompt, text):
        pass