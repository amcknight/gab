from story.limbic import Limbic
from story.face import Face
from story.message import Go
from story.worker import Worker


class Head:
    def __init__(self):
        self.limbic = Limbic.start()
        self.face = Face.start()
        self.cortex = [Worker.start() for _ in range(3)]

    def run(self):
        self.limbic.tell(Go(""))
