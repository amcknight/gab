class Message:
    def __init__(self, name):
        self.name = name

    def named(self, name):
        return name == self.name

# Face

class Say(Message):
    def __init__(self, name, mp3_path):
        super().__init__(name)
        self.mp3_path = mp3_path


class Hear(Message):
    def __init__(self, name, duration):
        super().__init__(name)
        self.duration = duration


# Limbic


class Go(Message):
    pass


class Story(Message):
    pass


class Prompt(Message):
    pass


class Heard(Message):
    def __init__(self, name, mp3_path):
        super().__init__(name)
        self.mp3_path = mp3_path


class Said(Message):
    def __init__(self, name, mp3_path):
        super().__init__(name)
        self.mp3_path = mp3_path


class Composed(Message):
    def __init__(self, name, text, mp3_path):
        super().__init__(name)
        self.text = text
        self.mp3_path = mp3_path


class Interpreted(Message):
    def __init__(self, name, mp3_path, text):
        super().__init__(name)
        self.mp3_path = mp3_path
        self.text = text


class Confabulated(Message):
    def __init__(self, name, prompt, text):
        super().__init__(name)
        self.prompt = prompt
        self.text = text


# Cortex

class TextToSpeech(Message):
    def __init__(self, name, text):
        super().__init__(name)
        self.text = text


class SpeechToText(Message):
    def __init__(self, name, mp3_path):
        super().__init__(name)
        self.mp3_path = mp3_path


class Complete(Message):
    def __init__(self, name, prompt, tokens):
        super().__init__(name)
        self.prompt = prompt
        self.tokens = tokens

