#!/usr/bin/env python

from __future__ import absolute_import
from os import environ, path
from ConfigParser import SafeConfigParser, NoSectionError
from optparse import Values

from mootils.common.debug import debug
from mootils.common.errors import *

def boolify(value):
	if isinstance(value, str) and len(value) > 3 and (value[1:] == "rue" or value[1:] == "alse"):
		return value[1:] == "rue"
	else: return value

class TypedConfigObject(object):
	""" This is intended to automagically create objects from a string read from a config file, if desired.
		if a TypedConfigObject is put into a ConfigDict, setting a value is passed to the set() method, which
		then creates an object from the parameter from the config.
	"""

	def __init__(self, value_type, defaultvalue):
		""" Construct a TypedConfigObject.

			@param value_type: The type used to create new instances of the config value.

			@param defaultvalue: The initial value, which this object is set to
			@type defaultvalue: value_type

		"""
		self.value_type = value_type
		self.set(defaultvalue)

	def set(self, args):
		if isinstance(args, tuple):
			if len(args) != 1: 
				debug('TypedConfigObject: len > 1')
				self.value = self.value_type(*args)
				return
			else: args = args[0] 
		if isinstance(args, self.value_type): self.value = args
		else:
			print args
			print self.value_type
			self.value = self.value_type(args)

	def __str__(self):
		return str(self.value)

class BoolConfigObject(TypedConfigObject):
	def __init__(self, defaultvalue=False):
		super(BoolConfigObject, self).__init__(bool, defaultvalue)

	def set(self, arg):
		super(BoolConfigObject, self).set(boolify(arg))

class ConfigDict(dict):
	def getitem(self, key):
		""" special method that is used in Configuration objects.
			Return the content of the TypedConfigObject wrapper, if it is present
		"""
		value = self[key]
		if isinstance(value, TypedConfigObject): value = value.value
		return value

	def __setitem__(self, key, value):
		""" TypedConfigObject instances get special treatment:
			If one would be overwritten, call its set() method instead.
			If the new value also is a TypedConfigObject, pass its value to set().
			If the key is new, try to create a TypedConfigObject.

		"""
		if not self.has_key(key):
			if isinstance(value, str) or isinstance(value, TypedConfigObject):
				pass
			elif isinstance(value, bool):
				value = BoolConfigObject(value)
			else:
				value = TypedConfigObject(type(value), value)
			super(ConfigDict, self).__setitem__(key, value)
		else:
			if isinstance(self[key], TypedConfigObject):
				if isinstance(value, TypedConfigObject): value = value.value
				self[key].set(value)
			else:
				super(ConfigDict, self).__setitem__(key, value)

	def update(self, newdict):
		for key, value in dict(newdict).iteritems(): self[key] = value

class Configuration(object):
	def __init__(self, **defaults):
		self.config_defaults  = ConfigDict()
		self.config_from_file = dict()
		self.config_from_cli  = ConfigDict()
		self.config			  = ConfigDict()

	def __getitem__(self, key):
		if not self.config.has_key(key):
			raise NoSuchOptionError(key)
		return self.config.getitem(key)

	def __str__(self):
		return str(self.config)

	def has_key(self, key):
		return self.config.has_key(key)

	@property
	def info(self):
		string = 'Defaults: %s\nCLI: %s\nFiles:' % (str(self.config_defaults), str(self.config_from_cli))
		for section, config in self.config_from_file.iteritems():
			string += '\nSection \'%s\': %s' % (section, str(config))
		return string

	def __rebuild_config(self):
		""" to be called after new values are added. """
		self.config = ConfigDict()
		self.config.update(self.config_defaults)
		for config in self.config_from_file.itervalues():
			self.config.update(config) 
		self.config.update(self.config_from_cli)

	def set_defaults(self, new_defaults):
		self.config_defaults.update(new_defaults)
		self.__rebuild_config()

	def set_cli_config(self, values):
		""" Set the config values read from command line invocation.

			@param values: Obtained from an instance of OptionParser. Its __dict__ contains all of the
						   possible command line options. If an option hasn't been supplied, it is
						   None, and thus not considered here.
			@type values: optparse.Values

		"""
		self.config_from_cli.update([key, value] for key, value in values.__dict__.iteritems() if value is not None)
		self.__rebuild_config()

	def set_file_config(self, section, file_config):
		if self.config_from_file.has_key(section): raise DuplicateFileSectionError(section)
		dups = [key for key in file_config.iterkeys() if any(config.has_key(key) for config in self.config_from_file.itervalues())]
		if len(dups) > 0:
			print "Warning: duplicate keys in file config: %s" % ", ".join(dups)
		self.config_from_file[section] = ConfigDict()
		self.config_from_file[section].update(file_config)
		self.__rebuild_config()

	def config_from_section(self, section, key):
		if not self.config_from_file.has_key(section): raise NoSuchSectionError(section)
		elif not self.config_from_file[section].has_key(key): raise NoSuchOptionError(key)
		else: return self.config_from_file[section][key]

class Configurable(object):
	config_files = []

	def __init__(self, *names):
		self.names = names
		self.config_parser = SafeConfigParser()
		self.__config = Configuration()
		self.config_parser.read(self.config_files)
		Configurations.register_config(self)

	@classmethod
	def add_config_files(cls, *files):
		cls.config_files.extend(files)

	def add_config_section(self, section, **defaults):
		self.__config.set_defaults(defaults)
		try:
			items = dict(self.config_parser.items(section))
			self.__config.set_file_config(section, items)
		except NoSectionError, e: debug(e)

	def config(self, key):
		if not self.__config.has_key(key):raise NoSuchOptionError(key)
		else: return self.__config[key]

	def config_from_section(self, section, key):
		return self.__config.config_from_section(section, key)

	def set_cli_config(self, items):
		self.__config.set_cli_config(items)

	def print_all(self):
		print self.__config.info

class ConfigClientNotYetConnectedError(MooException):
	def __init__(self, name, key):
		error_string = 'Config Client \'%s\' wasn\'t connected when accessing config option \'%s\'!' % (name, key)
		super(ConfigClientNotYetConnectedError, self).__init__(error_string)

class ConfigClientBase(object):
	def init(self, name):
		self.connected = False
		self.register(name)

	def register(self, name):
		self.name = name
		Configurations.register_client(self)
		return self

	def connect(self, config):
		if not self.connected:
			self._config = config
			self.connected = True

class ConfigClient(ConfigClientBase):
	def __init__(self, name):
		super(ConfigClient, self).init(name)

	def config(self, key):
		if not self.connected: raise ConfigClientNotYetConnectedError(self.name, key)
		return self._config.config(key)

	def __call__(self, key):
		return self.config(key)

class CLIConfig(ConfigClientBase):
	def __init__(self, name, values = None):
		self.init_cli_config(name, values)
	
	def init_cli_config(self, name, values = None):
		self.config_transferred = False
		self.config_set = False
		super(CLIConfig, self).init(name)
		self.set_cli_config(values)

	def set_cli_config(self, values):
		if values is not None:
			assert(isinstance(values, Values))
			self.values = values
			self.config_set = True
			self.__transfer_config()
		return self

	def connect(self, config):
		super(CLIConfig, self).connect(config)
		self.__transfer_config()
	
	def __transfer_config(self):
		if self.connected and self.config_set: self._config.set_cli_config(self.values)

class Configurations(object):
	configs = { }
	pending_clients = { }

	@classmethod
	def register_config(cls, config):
		for name in config.names:
			cls.configs[name] = config
			cls.notify_clients(name)

	@classmethod
	def register_client(cls, client):
		try: client.connect(cls.configs[client.name])
		except KeyError:
			if not cls.pending_clients.has_key(client.name): cls.pending_clients[client.name] = [ ]
			cls.pending_clients[client.name].append(client)

	@classmethod
	def notify_clients(cls, name):
		if cls.pending_clients.has_key(name):
			for client in cls.pending_clients[name]: client.connect(cls.configs[name])
			del cls.pending_clients[name]
