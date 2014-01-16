import signal
import sys
import threading
import functools

from tek import dodebug, logger
from tek.errors import MooException


class Singleton(type):

    @property
    def instance(cls):
        if cls._instance is None:
            cls._instance = SignalManager()
        return cls._instance


class SignalManager(metaclass=Singleton):
    _instance = None

    def __init__(self):
        if SignalManager._instance is not None:
            raise MooException('Tried to instantiate singleton SignalManager!')
        self._handlers = dict()
        self.exit_on_interrupt = True

    def sigint(self, handler=None):
        if handler is None:
            handler = lambda s, f: True
        self.add(signal.SIGINT, handler)

    def add(self, signum, handler):
        if threading.current_thread().name == 'MainThread':
            signal.signal(signum, self.handle)
        self._handlers.setdefault(signum, []).append(handler)

    def remove(self, handler):
        for sig in self._handlers.values():
            try:
                sig.remove(handler)
            except ValueError:
                pass

    def handle(self, signum, frame):
        logger.error('Interrupted by signal {}'.format(signum))
        for handler in reversed(self._handlers.get(signum, [])):
            handler(signum, frame)
        signal.signal(signum, signal.SIG_IGN)
        if signum == signal.SIGINT and self.exit_on_interrupt:
            sys.exit()


def moo_run(func, handle_sigint=True, *a, **kw):
    try:
        if handle_sigint:
            SignalManager.instance.sigint()
        func(*a, **kw)
    except MooException as e:
        logger.error(e)
    except Exception as e:
        logger.error(e)
        if dodebug:
            raise


def cli(func):
    @functools.wraps(func)
    def wrapper(*a, **kw):
        return moo_run(func, *a, **kw)
    return wrapper

__all__ = ['SignalManager', 'cli']
