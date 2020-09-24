from pykka import ActorRegistry


def face():
    return _first("Face")


def limbic():
    return _first("Limbic")


def cortex():
    return _first("Cortex")


def _first(class_name):
    return ActorRegistry.get_by_class_name(class_name)[0]