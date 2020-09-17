import pykka

"""Orchestrates the actions of the Cortex and Face"""
class Limbic(pykka.ThreadingActor):

    tags = None
    tag_confirmation_text = None
    tags_confirmed = False
    prompt_text = None
    prompt_path = None
    prompt_confirmed = False
    story_start_text = None
    story_start_path = None
    tag_audio_path = "story/input_audio/tag"
    yesno_audio_path = "story/input_audio/yesno"
    pages = []

    def on_receive(self, message):
        cmd, msg = message
        if cmd == "go":
            self.go()
        elif cmd == "prompt":
            self.prompt()
        elif cmd == "story":
            self.story()
        elif cmd == "heard":
            id, mp3_path = msg
            self.heard(id, mp3_path)
        elif cmd == "said":
            id, mp3_path = msg
            self.said(id, mp3_path)
        elif cmd == "composed":
            id, text, mp3_path = msg
            self.composed(id, text, mp3_path)
        elif cmd == "interpreted":
            id, mp3_path, text = msg
            self.interpreted(id, mp3_path, text)
        elif cmd == "confabulated":
            id, prompt, text = msg
            self.confabulated(id, prompt, text)
        else:
            raise Exception("Unknown Limbic command: " + cmd)

    def go(self):
        face = pykka.ActorRegistry.get_by_class_name("Face")[0]
        face.tell(("say", ("intro", "story/res/intro.mp3")))
        face.tell(("hear", ("get_tags", 5)))

    def prompt(self):
        if self.prompt_path:
            self.pages.append(self.prompt_text)
            face = pykka.ActorRegistry.get_by_class_name("Face")[0]
            worker = pykka.ActorRegistry.get_by_class_name("Worker")[0]
            face.tell(("say", ("first_page", self.prompt_path)))
            face.tell(("say", ("continue", "story/res/continue.mp3")))
            face.tell(("hear", ("prompt_confirmation", 2)))
            worker.tell(("complete", ("page", "".join(self.pages), 200)))
        else:
            self.actor_ref.tell(("prompt", None))

    def story(self):
        if self.prompt_confirmed:
            face = pykka.ActorRegistry.get_by_class_name("Face")[0]
            face.tell(("say", (id, self.story_start_path)))
        else:
            self.actor_ref.tell(("story", self.story_start_path))


    def heard(self, id, mp3_path):
        worker = pykka.ActorRegistry.get_by_class_name("Worker")[0]
        if id == "get_tags":
            worker.tell(("s2t", ("get_tags", mp3_path)))
        elif id == "tag_confirmation":
            worker.tell(("s2t", ("tag_confirmation", mp3_path)))
        elif id == "prompt_confirmation":
            worker.tell(("s2t", ("prompt_confirmation", mp3_path)))
        else:
            raise Exception("An unknown thing was heard! Creeeepy.")

    def said(self, id, mp3_path):
        if id == "page":
            worker = pykka.ActorRegistry.get_by_class_name("Worker")[0]
            worker.tell(("complete", ("page", "".join(self.pages), 200)))
        else:
            pass

    def composed(self, id, text, mp3_path):
        face = pykka.ActorRegistry.get_by_class_name("Face")[0]
        if id == "tag_confirmation":
            if self.tags_confirmed:
                raise Exception("Trying to confirm tags after they've been confirmed")

            face.tell(("say", (id, mp3_path)))
            face.tell(("hear", ("tag_confirmation", 2)))
        elif id == "story_prompt":
            if self.prompt_path:
                raise Exception("Trying to generate story prompt audio when it already exists")

            self.prompt_path = mp3_path
        elif id == "first_page":
            self.story_start_path = mp3_path
        elif id == "page":
            face.tell(("say", (id, mp3_path)))
        else:
            raise Exception("Unknown text was converted into audio")

    def interpreted(self, id, mp3_path, text):
        if id == "get_tags":
            if not text or text == "":
                self.actor_ref.tell(("go", None))
            else:
                self.set_tags(text)
                worker = pykka.ActorRegistry.get_by_class_name("Worker")[0]
                worker.tell(("t2s", ("tag_confirmation", self.tag_confirmation_text)))
                worker.tell(("complete", ("tag_prompt", self.get_prompt(), 100)))
        elif id == "tag_confirmation":
            if self.tags_confirmed:
                raise Exception("Trying to confirm tags after they've been confirmed")

            if text == "Yes.":
                self.tags_confirmed = True
                self.actor_ref.tell(("prompt", None))
            elif text == "No.":
                raise Exception("You can't SAY no to ME!!")
            else:
                face = pykka.ActorRegistry.get_by_class_name("Face")[0]
                face.tell(("say", ("tag_confirmation", mp3_path)))
                face.tell(("hear", ("tag_confirmation", 2)))
        elif id == "prompt_confirmation":
            if self.prompt_confirmed:
                raise Exception("Trying to confirm prompt after it's been confirmed")

            if text == "Yes.":
                self.prompt_confirmed = True
                self.actor_ref.tell(("story", None))
            elif text == "No.":
                raise Exception("You can't SAY no to ME!!!")
            else:
                face = pykka.ActorRegistry.get_by_class_name("Face")[0]
                face.tell(("say", ("prompt_confirmation", mp3_path)))
                face.tell(("hear", ("prompt_confirmation", 2)))
        else:
            raise Exception("Interpreted some unknown audio... voice in my head?")

    def confabulated(self, id, prompt, text):
        worker = pykka.ActorRegistry.get_by_class_name("Worker")[0]
        if id == "tag_prompt":
            if self.prompt_text:
                raise Exception("Trying to set prompt text when it already exists")

            self.prompt_text = text
            worker.tell(("t2s", ("story_prompt", text)))
        elif id == "first_page":
            self.story_start_text = text
            worker.tell(("t2s", (id, text)))
        elif id == "page":
            self.pages.append(text)
            worker.tell(("t2s", (id, text)))
        else:
            raise Exception("Unknown thing was confabulated. Am I ruminating?")

    def set_tags(self, text):
        if self.tags:
            raise Exception("Trying to set tags when already set")

        if text[-4:] == " and":
            text = text[-4:]
        self.tags = text.split(" and ")
        self.tag_confirmation_text = "Would you like to hear a story about " + self.andify(self.tags) + "?"

    def andify(self, ts):
        if len(ts) == 0:
            return ""
        if len(ts) == 1:
            return ts[0]
        tags2 = ts.copy()
        tags2[-1] = "and " + ts[-1]
        return ", ".join(tags2)

    def get_prompt(self):
        with open("story/res/tag2prompt.txt") as t2p_file:
            data = t2p_file.read()

        return data + "\n\n[tags] " + ", ".join(self.tags) + "\n[prompt]"
