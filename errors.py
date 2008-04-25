from __future__ import with_statement

class MooException(Exception):
	pass

class NotImplementedError(MooException):
	pass

class NoOverloadError(NotImplementedError):
	def __init__(self, function, obj):
		error_msg = '%s cannot handle parameters of type %s!' \
					% (function, type(obj))
		super(NoOverloadError, self).__init__(error_msg)

class ConfigError(MooException): pass

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
		super(DuplicateFileSectionError, self).__init__('Config file section \'%s\' already added!' % section)

