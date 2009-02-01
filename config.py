#!/usr/bin/env python

from __future__ import absolute_import
from os import environ, path
from ConfigParser import SafeConfigParser, NoSectionError
from optparse import Values

from tek.debug import debug
from tek.errors import *

def boolify(value):
    """ Return a string's boolean value if it is a string and "true" or
    "false"(case insensitive), else just return the object.
    
    """
    if isinstance(value, str) and len(value) > 3 and \
       (value.lower() == 'true' or value.lower() == 'false'):
        return value.lower() == 'true'
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
        """ Assign args as the config object's value.
        If args is not of the value_type of the config object, it is
        passed to value_type.__init__. args may be a tuple of 
        parameters.
        
        """
        if isinstance(args, tuple):
            if len(args) != 1: 
                debug('TypedConfigObject: len > 1')
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

class BoolConfigObject(TypedConfigObject):
    """ Specialization of TypedConfigObject for booleans, as they must
    be parsed from strings differently.
    
    """
    def __init__(self, defaultvalue=False):
        """ Set the value_type to bool.
        
        """
        super(BoolConfigObject, self).__init__(bool, defaultvalue)

    def set(self, arg):
        """ Transform arg into a bool value and pass it to super.
        
        """
        super(BoolConfigObject, self).set(boolify(arg))

class ConfigDict(dict):
    """ Dictionary, that respects TypedConfigObjects when getting or
    setting.
    
    """
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
        """ Convenience overload.
        
        """
        for key, value in dict(newdict).iteritems(): self[key] = value

class Configuration(object):
    """ Container for several dictionaries representing configuration
    options from various sources:
    - The defaults, to be set from a Configurable instance
    - The file config, read from all files given in the Configurable
    - The command line options, passed by a CLIConfig object through
    the static Configurations proxy class.
    It can be used from Configurable and ConfigClient derivatives to
    obtain the value to a config key, where the precedence is
    cli->files->defaults.
    Different section names can be used for groups of options from the
    Configurable, which correspond to the section names from the files.
    
    """
    def __init__(self, **defaults):
        """ Initialize the dicts used to store the config and the list
        of section names that are added for defaults.
        
        """
        self.sections         = list()
        self.config_defaults  = dict()
        self.config_from_file = dict()
        self.config_from_cli  = ConfigDict()
        self.config           = ConfigDict()

    def __getitem__(self, key):
        """ Emulate read-only container behaviour.
        
        """
        if not self.config.has_key(key):
            raise NoSuchOptionError(key)
        return self.config.getitem(key)

    def __str__(self):
        return str(self.config)

    def has_key(self, key):
        """ Emulate read-only container behaviour.
        
        """
        return self.config.has_key(key)

    @property
    def info(self):
        """ Return the contents of all sources and sections.
        
        """
        string = 'Defaults: %s\nCLI: %s\nFiles:' % (str(self.config_defaults),
                                                    str(self.config_from_cli))
        for section, config in self.config_from_file.iteritems():
            string += '\nSection \'%s\': %s' % (section, str(config))
        return string

    def __rebuild_config(self):
        """ Collect the config options from the defaults, the file
        config sections that have been default-added and the cli
        config in that order and store them in self.config.
        The defaults and file config sections are iterated in the 
        order of the additions of the defaults.
        To be called after new values are added.
        
        """
        self.config = ConfigDict()

        # defaults and file config
        for section in self.sections:
            self.config.update(self.config_defaults[section])
            if self.config_from_file.has_key(section):
                self.config.update(self.config_from_file[section])

        # cli overrides
        valid_pairs = [[key, value] for 
                       key, value in self.config_from_cli.iteritems() 
                       if any(conf.has_key(key) for 
                       conf in self.config_defaults.values())]
        self.config.update(valid_pairs)

    def set_defaults(self, section, new_defaults):
        """ Add a new unique section with default values to the list of
        default options.

        """
        if self.config_from_file.has_key(section): 
            raise DuplicateDefaultSectionError(section)
        self.sections.append(section)
        self.config_defaults[section] = ConfigDict()
        self.config_defaults[section] = new_defaults
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
        """ Add the values of a given section from the files uniquely
        as a ConfigDict object and rebuild the main config.
        
        """
        if self.config_from_file.has_key(section): 
            raise DuplicateFileSectionError(section)
        dups = [key for key in file_config.iterkeys() 
                if any(config.has_key(key) for config 
                       in self.config_from_file.itervalues())]
        if len(dups) > 0:
            print "Warning: duplicate keys in file config: %s" % ", ".join(dups)
        self.config_from_file[section] = ConfigDict()
        self.config_from_file[section].update(file_config)
        self.__rebuild_config()

    def config_from_section(self, section, key):
        """ Obtain the value that key has in the specific section,
        in the order file->default.
        
        """
        if not self.has_section(section):
            raise NoSuchSectionError(section)
        elif self.config_from_file.has_key(section) and \
             self.config_from_file[section].has_key(key): 
            return self.config_from_file[section][key]
        elif not self.config_defaults[section].has_key(key): 
            raise NoSuchOptionError(key)
        else:
            return self.config_defaults[section][key]

    def has_section(self, name):
        """ Return True if a section with name has been added.
        
        """
        return name in self.sections

class Configurable(object):
    """ Class that represents a part of the program with configurable
    options.
    config_files should be set through add_config_files if files should
    be read into the config.
    A Configurable is identified by a number of names, so that a
    ConfigClient can access it through the Configurations singleton.
    
    """
    config_files = []

    def __init__(self, *names):
        """ Set the names that should identify this part of the config,
        init the file parser and Configuration instance, read out the
        files and register with the Configurations proxy.
        
        """
        self.names = names
        self.config_parser = SafeConfigParser()
        self.__config = Configuration()
        self.config_parser.read(self.config_files)
        Configurations.register_config(self)

    @classmethod
    def add_config_files(cls, *files):
        """ Add a file path to the config file list.
        
        """
        cls.config_files.extend(files)

    def add_config_section(self, section, **defaults):
        """ Add a section with optional default values to the config.
        If section is present in the file config, read it and pass it
        to the config.
        
        """
        self.__config.set_defaults(section, defaults)
        try:
            items = dict(self.config_parser.items(section))
            self.__config.set_file_config(section, items)
        except NoSectionError, e: 
            debug('ConfigParser: ' + str(e))

    def config(self, key, default=None):
        """ Obtain the value of a config option.
        
        """
        if not self.__config.has_key(key):
            if default is not None:
                return default
            else:
                raise NoSuchOptionError(key)
        else: return self.__config[key]

    def config_has_section(self, name):
        return self.__config.has_section(name)

    def config_from_section(self, section, key):
        return self.__config.config_from_section(section, key)

    def set_cli_config(self, items):
        """ Pass the values of the command line options to the config.
        
        """
        self.__config.set_cli_config(items)

    def print_all(self):
        print self.__config.info

class ConfigClientNotYetConnectedError(MooException):
    """ This error is thrown if a ConfigClient instance tries to get a
    config value before the corresponding Configurable hadn't yet been
    initialized and connected.
    
    """
    def __init__(self, name, key):
        error_string = 'Config Client \'%s\' wasn\'t connected when accessing config option \'%s\'!' % (name, key)
        super(ConfigClientNotYetConnectedError, self).__init__(error_string)

class ConfigClientBase(object):
    """ A class which allows remote access to a Configuration.

    """
    def _init(self, name):
        """ Must be called from subclasses.
        
        """
        self.connected = False
        self.register(name)

    def register(self, name):
        """ Add self to the list of instances waiting for the 
        Configurable in the Configurations proxy.

        """
        self.name = name
        Configurations.register_client(self)
        return self

    def connect(self, config):
        """ Reference the Configuration instance as the config to be
        used by the client. Called from Configurations once the 
        Configurable is ready.
        Mark as connected, so that the config isn't switched.
        
        """
        if not self.connected:
            self._config = config
            self.connected = True

class ConfigClient(ConfigClientBase):
    """ Standard read-only proxy for a Configuration.
    
    """
    def __init__(self, name):
        """ Connect to the Configuration called name.
        
        """
        super(ConfigClient, self)._init(name)

    def config(self, key):
        """ Obtain a config option's value.
        
        """
        if not self.connected: 
            raise ConfigClientNotYetConnectedError(self.name, key)
        return self._config.config(key)

    def __call__(self, key):
        return self.config(key)

class CLIConfig(ConfigClientBase):
    """ Proxy for setting the command line arguments as config values.
    
    """
    def __init__(self, name, values = None):
        self.init_cli_config(name, values)
    
    def init_cli_config(self, name, values = None):
        """ Connect to the config called name and optionally send the
        cli values if already present.
        
        """
        self.config_transferred = False
        self.config_set = False
        super(CLIConfig, self)._init(name)
        self.set_cli_config(values)

    def set_cli_config(self, values):
        """ If present, set the values attribute and transfer them.
        
        """
        if values is not None:
            assert(isinstance(values, Values))
            self.values = values
            self.config_set = True
            self.__transfer_config()
        return self

    def connect(self, config):
        """ Call super and try to send the config.
        
        """
        super(CLIConfig, self).connect(config)
        self.__transfer_config()
    
    def __transfer_config(self):
        """ Pass the cli values to the Configurations singleton, if
        the Configurable has already completed setup.
        
        """
        if self.connected and self.config_set:
            self._config.set_cli_config(self.values)

class Configurations(object):
    """ Program-wide register of Configurable instances.
    Connects the clients to the according Configurable, as soon as it
    has registered.

    """
    # A dict of Configurable instances by their name
    configs = { }

    # A dict of lists of client instances grouped by the name of the
    # target Configurable's name
    pending_clients = { }

    @classmethod
    def register_config(cls, config):
        """ Add a Configurable instance to the configs dict under each 
        of its names and connect waiting client instances.

        """
        assert(isinstance(config, Configurable))
        for name in config.names:
            cls.configs[name] = config
            cls.notify_clients(name)

    @classmethod
    def register_client(cls, client):
        """ Connect a client instance to the according Configurable 
        instance, buffering the request if neccessary.

        """
        try: client.connect(cls.configs[client.name])
        except KeyError:
            if not cls.pending_clients.has_key(client.name): cls.pending_clients[client.name] = [ ]
            cls.pending_clients[client.name].append(client)

    @classmethod
    def notify_clients(cls, name):
        """ Connects clients to Configurable 'name' that have been
        registered before their target and clear the client dict item.

        """
        if cls.pending_clients.has_key(name):
            for client in cls.pending_clients[name]: 
                client.connect(cls.configs[name])
            del cls.pending_clients[name]
