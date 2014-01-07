import os
import shutil

import spec

from tek import Configurations
from tek.tools import touch

Configurations.enable_lazy_class_attr = False

__base_dir__ = None


def setup(_path):
    ''' Use the supplied path to initialise the tests base dir.
    If _path is a file, its dirname is used.
    '''
    if not os.path.isdir(_path):
        _path = os.path.dirname(_path)
    global __base_dir__
    __base_dir__ = _path


def create_temp_file(*components):
    _file = temp_file(*components)
    return touch(_file)


def temp_file(*components):
    return os.path.join(temp_dir(*components[:-1]), *components[-1:])


def temp_path(*components):
    return os.path.join(__base_dir__, '_temp', *components)


def temp_dir(*components):
    _dir = temp_path(*components)
    os.makedirs(_dir, exist_ok=True)
    return _dir


def fixture_path(*components):
    return os.path.join(__base_dir__, '_fixtures', *components)


def load_fixture(*components):
    with open(fixture_path(*components), 'r') as f:
        return f.read()


class Spec(spec.Spec):

    def setup(self, *a, **kw):
        if __base_dir__:
            shutil.rmtree(temp_path(), ignore_errors=True)


__all__ = ['create_temp_file', 'temp_file', 'temp_path', 'temp_dir',
           'fixture_path', 'load_fixture', 'Spec']
