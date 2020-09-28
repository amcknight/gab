import functools
import logging

dispatcher = {}


def on(event_type=None, event_name=None, state=None):
    def dec(func):
        dispatcher[(event_type, event_name, state)] = func

        @functools.wraps(func)
        def wrapper(event):
            # TODO: Should be able to pass in log level
            logging.info(type(event).__name__ + ", " + event.name + ", " + state.name)
            return func(event)

        return wrapper

    return dec
