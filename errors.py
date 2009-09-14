""" {{{ Copyright (c) 2009 Torsten Schmits

This file is part of pytek. pytek is free software;
you can redistribute it and/or modify it under the terms of the GNU General
Public License version 2, as published by the Free Software Foundation.

pytek is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
details.

You should have received a copy of the GNU General Public License along with
this program; if not, write to the Free Software Foundation, Inc., 59 Temple
Place, Suite 330, Boston, MA  02111-1307  USA

}}} """

from __future__ import with_statement

class MooException(Exception):
    pass

class NoOverloadError(NotImplementedError):
    def __init__(self, function, obj):
        error_msg = '%s cannot handle parameters of type %s!' \
                    % (function, type(obj))
        super(NoOverloadError, self).__init__(error_msg)

class ConfigError(MooException): 
    pass

class NoSuchOptionError(ConfigError):
    def __init__(self, key):
        super(NoSuchOptionError, self).__init__('No such config option: %s' % key)

class DuplicateDefaultError(ConfigError):
    def __init__(self, key):
        super(DuplicateDefaultError, self).__init__('Default config option already set: %s' % key)

class NoSuchConfigError(ConfigError):
    def __init__(self, name):
        super(NoSuchConfigError, self).__init__('No Configurable registered under the name %s' % name)

class NoSuchSectionError(ConfigError):
    def __init__(self, section):
        super(NoSuchSectionError, self).__init__('No section named \'%s\' had been loaded!' % section)

class MultipleSectionsWithKeyError(ConfigError):
    def __init__(self, key):
        super(MultipleConfigSectionsWithKeyError, self).__init__('More than one section contain an option with the value %s' % key)

class DuplicateFileSectionError(ConfigError):
    def __init__(self, section):
        super(DuplicateFileSectionError, self).__init__(
                'Config file section \'%s\' already added!' % section)

class DuplicateDefaultSectionError(ConfigError):
    def __init__(self, section):
        super(DuplicateDefaultSectionError, self).__init__(
                'Config defaults section \'%s\' already added!' % section)

class ConfigClientNotYetConnectedError(ConfigError):
    """ This error is thrown if a ConfigClient instance tries to get a
    config value before the corresponding Configurable hadn't yet been
    initialized and connected.
    
    """
    def __init__(self, name, key):
        error_string = 'Config Client \'%s\' wasn\'t connected when accessing config option \'%s\'!' % (name, key)
        super(ConfigClientNotYetConnectedError, self).__init__(error_string)

class InternalError(MooException):
    pass

