import os
import shutil
import warnings
from datetime import datetime
import time
from pathlib import Path

import spec

from tek import Config
from tek.tools import touch
from tek.errors import Error

Config.enable_lazy_class_attr = False

__base_dir__ = None


class TestEnvError(Error):
    pass


def setup(path):
    ''' Use the supplied path to initialise the tests base dir.
    If _path is a file, its dirname is used.
    '''
    if not isinstance(path, Path):
        path = Path(path)
    if not path.is_dir():
        path = path.parent
    global __base_dir__
    __base_dir__ = path


def _check():
    if __base_dir__ is None:
        msg = 'Test base dir not set! Call tek.test.setup(dir).'
        raise TestEnvError(msg)


def temp_path(*components):
    _check()
    return Path(__base_dir__, '_temp', *components)


def temp_dir(*components):
    _dir = temp_path(*components)
    _dir.mkdir(exist_ok=True, parents=True)
    return _dir


def temp_file(*components):
    return temp_dir(*components[:-1]).joinpath(*components[-1:])


def create_temp_file(*components):
    _file = temp_file(*components)
    _file.touch()
    return _file


def fixture_path(*components):
    _check()
    return Path(__base_dir__, '_fixtures', *components)


def load_fixture(*components):
    with fixture_path(*components).open() as f:
        return f.read()


def later(ass, timeout=5, intval=0.1):
    start = datetime.now()
    ok = False
    while not ok and (datetime.now() - start).total_seconds() < timeout:
        try:
            ass()
            ok = True
        except AssertionError:
            time.sleep(intval)
    return ass()


class Spec(spec.Spec):

    def __init__(self, configs=['tek'], *a, **kw):
        self._configs = configs
        self._warnings = True

    def setup(self, *a, allow_files=False, **kw):
        if __base_dir__:
            shutil.rmtree(str(temp_path()), ignore_errors=True)
        if self._warnings:
            warnings.resetwarnings()
        Config.allow_files = allow_files
        Config.setup(*self._configs, files=allow_files)
        Config.override('general', debug=True)

    def teardown(self, *a, **kw):
        warnings.simplefilter('ignore')

    def _wait_for(self, pred, timeout=5, intval=0.1):
        start = datetime.now()
        while (not pred() and
               (datetime.now() - start).total_seconds() < timeout):
            time.sleep(intval)
        pred().should.be.ok


__all__ = ['create_temp_file', 'temp_file', 'temp_path', 'temp_dir',
           'fixture_path', 'load_fixture', 'Spec']
