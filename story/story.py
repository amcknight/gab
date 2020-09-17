import pykka

# Creates the Head and wakes it up
from story.limbic import Limbic
from story.face import Face
from story.worker import Worker

import logging
logging.basicConfig(level=logging.WARN)

def run():
    limbic = Limbic.start()
    Face.start()
    Worker.start()
    limbic.tell(("go", None))
