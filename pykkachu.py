import functools
import logging
from pykka import ThreadingActor
from pysm import StateMachine

dispatchers = {}


class Dispatcher:
    funcs = {}

    def add(self, func, event_type=None, event_name=None, state=None):
        if (event_type, event_name, state) in self.funcs:
            raise Exception("Can't have two event processors with the same trigger")

        self.funcs[(event_type, event_name, state)] = func

    def get(self, event_type=None, event_name=None, state=None):
        if (event_type, event_name, state) in self.funcs:
            return self.funcs[(event_type, event_name, state)]
        elif (event_type, event_name, None) in self.funcs:
            return self.funcs[(event_type, event_name, None)]
        elif (event_type, None, state) in self.funcs:
            return self.funcs[(event_type, None, state)]
        elif (None, event_name, state) in self.funcs:
            return self.funcs[(None, event_name, state)]
        elif (event_type, None, None) in self.funcs:
            return self.funcs[(event_type, None, None)]
        elif (None, event_name, None) in self.funcs:
            return self.funcs[(None, event_name, None)]
        elif (None, None, state) in self.funcs:
            return self.funcs[(None, None, state)]
        elif (None, None, None) in self.funcs:
            return self.funcs[(None, None, None)]
        else:
            raise Exception("No function to dispatch to")


class Fleet(ThreadingActor):
    num_msgs = 0

    def __init__(self, actor, num):
        super().__init__()
        self.num = num
        self.actors = [actor.start() for _ in range(self.num)]

    def on_receive(self, msg):
        self.num_msgs += 1
        index = self.num_msgs % self.num
        self.actors[index].tell(msg)


class Actor(ThreadingActor):
    def __init__(self):
        super().__init__()
        self.sm = StateMachine("sm")

    def on_receive(self, msg):
        event_type = type(msg)
        event_name = msg.name
        try:
            dispatchers[_klass(self)].get(event_type, event_name, self.sm.state)(self, msg)
        except:
            raise Exception("function undispatchable: " + str(msg) + ", " + str(self.sm.state))


def on(event_type=None, event_name=None, state=None):
    def dec(func):
        trigger = (event_type, event_name, state)
        kls = _klass_func(func)
        if kls not in dispatchers:
            dispatchers[kls] = Dispatcher()

        dispatchers[kls].add(func, event_type, event_name, state)

        @functools.wraps(func)
        def wrapper(*args):
            # TODO: Should be able to pass in log level
            logging.info(map(str, list(trigger)))
            return func(*args)

        return wrapper

    return dec


def _klass(kls):
    return type(kls).__qualname__


def _klass_func(func):
    return ".".join(func.__qualname__.split('.')[:-1])