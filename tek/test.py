import os
import shutil
import warnings
from datetime import datetime
import time

import spec

from tek import Config
from tek.tools import touch
from tek.errors import Error

Config.enable_lazy_class_attr = False

__base_dir__ = None


class TestEnvError(Error):
    pass


def setup(_path):
    ''' Use the supplied path to initialise the tests base dir.
    If _path is a file, its dirname is used.
    '''
    if not os.path.isdir(_path):
        _path = os.path.dirname(_path)
    global __base_dir__
    __base_dir__ = _path


def _check():
    if __base_dir__ is None:
        msg = 'Test base dir not set! Call tek.test.setup(dir).'
        raise TestEnvError(msg)


def create_temp_file(*components):
    _file = temp_file(*components)
    return touch(_file)


def temp_file(*components):
    return os.path.join(temp_dir(*components[:-1]), *components[-1:])


def temp_path(*components):
    _check()
    return os.path.join(__base_dir__, '_temp', *components)


def temp_dir(*components):
    _dir = temp_path(*components)
    os.makedirs(_dir, exist_ok=True)
    return _dir


def fixture_path(*components):
    _check()
    return os.path.join(__base_dir__, '_fixtures', *components)


def load_fixture(*components):
    with open(fixture_path(*components), 'r') as f:
        return f.read()


class Spec(spec.Spec):

    def __init__(self, configs=['tek'], *a, **kw):
        self._configs = configs

    def setup(self, *a, allow_files=False, **kw):
        if __base_dir__:
            shutil.rmtree(temp_path(), ignore_errors=True)
        warnings.resetwarnings()
        Config.allow_files = allow_files
        Config.enable_lazy_class_attr = False
        Config.setup(*self._configs, files=allow_files)
        Config.override('general', debug=True)

    def teardown(self, *a, **kw):
        warnings.simplefilter('ignore')

    def _wait_for(self, pred, timeout=5):
        start = datetime.now()
        while (not pred() and
               (datetime.now() - start).total_seconds() < timeout):
            time.sleep(1)
        pred().should.be.ok


__all__ = ['create_temp_file', 'temp_file', 'temp_path', 'temp_dir',
           'fixture_path', 'load_fixture', 'Spec']
