from pykka import ActorRegistry


def face():
    return _first("Face")


def limbic():
    return _first("Limbic")


def cortex():
    return ActorRegistry.get_by_class_name("Worker")


def _first(class_name):
    return ActorRegistry.get_by_class_name(class_name)[0]