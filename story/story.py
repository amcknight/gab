import pykka

# Creates the Head and wakes it up
from story.limbic import Limbic
from story.face import Face
from story.message import Go
from story.worker import Worker
import logging

logging.basicConfig(level=logging.INFO)
logging.getLogger('pykka').setLevel(logging.INFO)


def run():
    limbic = Limbic.start()
    Face.start()
    Worker.start()
    limbic.tell(Go(""))
