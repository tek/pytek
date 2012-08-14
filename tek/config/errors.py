__copyright__ = """ Copyright (c) 2011-2012 Torsten Schmits

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

from tek.errors import MooException

class ConfigError(MooException): 
    pass

class NoSuchOptionError(ConfigError):

    def __init__(self, key):
        super(NoSuchOptionError, self).__init__('No such config option: %s' % key)

class DuplicateDefaultError(ConfigError):

    def __init__(self, key):
        super(DuplicateDefaultError, self).__init__('Default config option already set: %s' % key)

class MultipleSectionsWithKeyError(ConfigError):

    def __init__(self, key):
        super(MultipleSectionsWithKeyError, self).__init__('More than one section contain an option with the value %s' % key)

class DuplicateFileSectionError(ConfigError):

    def __init__(self, section):
        super(DuplicateFileSectionError, self).__init__(
                'Config file section \'%s\' already added!' % section)

class DuplicateDefaultSectionError(ConfigError):

    def __init__(self, section):
        super(DuplicateDefaultSectionError, self).__init__(
                'Config defaults section \'%s\' already added!' % section)

class NoSuchConfigError(ConfigError):

    def __init__(self, name):
        super(NoSuchConfigError, self).__init__('No Configurable registered under the name %s' % name)

class NoSuchSectionError(ConfigError):

    def __init__(self, section):
        super(NoSuchSectionError, self).__init__('No section named \'%s\' had been loaded!' % section)

class ConfigClientNotYetConnectedError(ConfigError):
    """ This error is thrown if a ConfigClient instance tries to get a
    config value before the corresponding Configurable hadn't yet been
    initialized and connected.
    
    """

    def __init__(self, name, key):
        error_string = 'Config Client \'%s\' wasn\'t connected when accessing config option \'%s\'!' % (name, key)
        super(ConfigClientNotYetConnectedError, self).__init__(error_string)

class ValueError(ConfigError):

    def __init__(self, typ, value):
        message = 'Invalid value \'{}\' for \'{}\'!'
        super(ValueError, self).__init__(message.format(typ, value))
