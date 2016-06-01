import signal
import sys
import threading
import functools
import inspect
import importlib
import logging

from tek import dodebug, logger, Config, dodebug
from tek.errors import TException
from tek.config.errors import ConfigLoadError

from tryp.logging import tryp_stdout_logging


class Singleton(type):

    @property
    def instance(cls):
        if cls._instance is None:
            cls._instance = SignalManager()
        return cls._instance


class SignalManager(metaclass=Singleton):
    _instance = None  # type: ignore

    def __init__(self):
        if SignalManager._instance is not None:
            raise TException('Tried to instantiate singleton SignalManager!')
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


def main(func, handle_sigint=True, *a, **kw):
    try:
        if handle_sigint:
            SignalManager.instance.sigint()
        return func(*a, **kw)
    except TException as e:
        logger.error(e)
    except Exception as e:
        logger.error(e)
        if dodebug:
            raise

moo_run = main


def _valid_parent_module(module):
    parent = module
    while parent:
        try:
            importlib.import_module('{}.config'.format(parent))
        except ImportError:
            parts = parent.rsplit('.', 1)
            if len(parts) == 1:
                msg = 'No parent module with config found for entry point {}'
                raise ConfigLoadError(msg.format(module))
            else:
                parent = parts[0]
        else:
            return parent


def _load_entry_point_config(module, config_alias=None, parse_cli=True,
                             positional=()):
    if config_alias is None:
        config_alias = _valid_parent_module(module)
    Config.setup(config_alias)
    if parse_cli:
        Config.parse_cli(positional=positional)
        conf = Config['general']
        if conf['stdout']:
            level = (logging.DEBUG if conf['debug'] else
                     logging.VERBOSE if conf['verbose'] else None)
            tryp_stdout_logging(level)
            if conf['debug']:
                global dodebug
                dodebug = True


def cli(load_config=True, **conf_kw):
    ''' Convenience decorator for entry point functions.
    Using this has two effects:
    The function is wrapped by the main() function that handles SIGINT
    and exceptions.
    If 'load_config' is True, the caller's module's config is loaded,
    and, if parse_cli is True, the command line arguments are parsed.
    Both parameters are true by default.
    The parameter 'positional' may specify positional arguments as used
    by Config.parse_cli().
    '''
    module = inspect.getmodule(inspect.stack()[1][0]).__package__

    def dec(func):
        @functools.wraps(func)
        def wrapper(*a, **kw):
            if load_config:
                _load_entry_point_config(module, **conf_kw)
            main(func, *a, **kw)
        return wrapper
    if hasattr(load_config, '__call__'):
        func = load_config
        load_config = False
        return dec(func)
    return dec

__all__ = ['SignalManager', 'cli', 'main']
