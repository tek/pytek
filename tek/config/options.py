__copyright__ = """ Copyright (c) 2011 Torsten Schmits

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation; either version 3 of the License, or (at your
option) any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, see <http://www.gnu.org/licenses/>.
"""

import os, glob

from tek import logger, debug
from tek.tools import join_lists

__all__ = ['BoolConfigOption', 'ListConfigOption', 'UnicodeConfigOption',
           'PathConfigOption', 'PathListConfigOption']

def boolify(value):
    """ Return a string's boolean value if it is a string and "true" or
    "false"(case insensitive), else just return the object.
    """
    try:
        return value.lower() == 'true'
    except:
        return bool(value)

class ConfigOption(object):
    def __init__(self, positional=None, short=None, **params):
        self.positional = positional
        self.short = short
        self.set_argparse_params(**params)

    def set_argparse_params(self, help=''):
        self._help = help
        self.help = help

    @property
    def argparse_params(self):
        p = dict()
        for name in ['help']:
            value = getattr(self, '_' + name, None)
            if value:
                p[name] = value
        return p

    def set_from_co(self, other):
        self.set_argparse_params(**other.argparse_params)
        if other.positional is not None:
            self.positional = other.positional
        if other.short is not None:
            self.short = other.short

    @property
    def effective_value(self):
        return self.value

class TypedConfigOption(ConfigOption):
    """ This is intended to automagically create objects from a string
    read from a config file, if desired. If a TypedConfigOption is put
    into a ConfigDict, setting a value is passed to the set() method,
    which then creates an object from the parameter from the config.
    """
    def __init__(self, value_type, defaultvalue, **params):
        """ Construct a TypedConfigOption.
            @param value_type: The type used to create new instances of
            the config value.
            @param defaultvalue: The initial value to which this object
            is set.
            @type defaultvalue: value_type
        """
        self.value_type = value_type
        self.set(defaultvalue)
        ConfigOption.__init__(self, **params)

    def set(self, args):
        """ Assign args as the config object's value.
        If args is not of the value_type of the config object, it is
        passed to value_type.__init__. args may be a tuple of 
        parameters.
        """
        if isinstance(args, tuple):
            if len(args) != 1: 
                logger.debug('TypedConfigOption: len > 1')
                self.value = self.value_type(*args)
                return
            else: args = args[0] 
        if isinstance(args, self.value_type): 
            self.value = args
        else:
            self.value = self.value_type(args)

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return str(self)

    def set_from_co(self, other):
        if other.value is not None:
            self.value = other.value
        ConfigOption.set_from_co(self, other)

class BoolConfigOption(TypedConfigOption):
    """ Specialization of TypedConfigOption for booleans, as they must
    be parsed from strings differently.
    """
    def __init__(self, defaultvalue=False, no=None, **params):
        """ Set the value_type to bool. """
        TypedConfigOption.__init__(self, bool, defaultvalue, **params)
        self.no = no

    def set_from_co(self, other):
        if other.no is not None:
            self.no = other.no
        TypedConfigOption.set_from_co(self, other)

    def set(self, arg):
        """ Transform arg into a bool value and pass it to super. """
        super(BoolConfigOption, self).set(boolify(arg))

class ListConfigOption(TypedConfigOption):
    def __init__(self, defaultvalue=None, splitchar=',', element_type=None,
                 **params):
        if defaultvalue is None:
            defaultvalue = []
        self._splitchar = splitchar
        self._element_type = element_type
        TypedConfigOption.__init__(self, list, defaultvalue, **params)

    def set(self, value):
        if isinstance(value, basestring):
            value = value.split(self._splitchar)
        if self._element_type is not None:
            value = map(self._element_type, value)
        self.value = value

    @property
    def effective_value(self):
        if self._element_type is not None:
            return [e.effective_value for e in self.value]
        else:
            return TypedConfigOption.effective_value.fget(self)

    def __str__(self):
        return self._splitchar.join(self.value)

class PathListConfigOption(ListConfigOption):
    def __init__(self, *a, **kw):
        t = PathConfigOption
        super(PathListConfigOption, self).__init__(*a, element_type=t, **kw)

    def set(self, value):
        super(PathListConfigOption, self).set(value)
        debug(self.value)
        globbed = map(glob.glob, [v.value for v in self.value])
        self.value = join_lists(globbed)

    @property
    def effective_value(self):
        return self.value

class UnicodeConfigOption(TypedConfigOption):
    def __init__(self, default, **params):
        TypedConfigOption.__init__(self, unicode, default, **params)

    def __str__(self):
        return self.value.encode('utf-8')

class PathConfigOption(UnicodeConfigOption):
    def __init__(self, path=None, **params):
        super(PathConfigOption, self).__init__(path or '', **params)

    def set(self, path):
        self.value = os.path.expandvars(os.path.expanduser(path))
