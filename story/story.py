from story.limbic import Limbic
from story.face import Face
from story.message import Go
from story.worker import Worker


# Builds the Head and wakes it up
def run():
    limbic = Limbic.start()
    Face.start()
    Worker.start()
    limbic.tell(Go(""))
