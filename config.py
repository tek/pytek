from __future__ import absolute_import
from os import environ, path
from ConfigParser import SafeConfigParser, NoSectionError
from optparse import Values

from tek.errors import *
from tek.log import logger

def boolify(value):
    """ Return a string's boolean value if it is a string and "true" or
    "false"(case insensitive), else just return the object.
    """
    try:
        return value.lower() == 'true'
    except:
        return bool(value)

class TypedConfigObject(object):
    """ This is intended to automagically create objects from a string
    read from a config file, if desired. If a TypedConfigObject is put
    into a ConfigDict, setting a value is passed to the set() method,
    which then creates an object from the parameter from the config.
    """
    def __init__(self, value_type, defaultvalue):
        """ Construct a TypedConfigObject.
            @param value_type: The type used to create new instances of
            the config value.  
            @param defaultvalue: The initial value, which this object is
            set to
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
                logger.debug('TypedConfigObject: len > 1')
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
        """ Set the value_type to bool. """
        super(BoolConfigObject, self).__init__(bool, defaultvalue)

    def set(self, arg):
        """ Transform arg into a bool value and pass it to super. """
        super(BoolConfigObject, self).set(boolify(arg))

class ListConfigObject(TypedConfigObject):
    def __init__(self, defaultvalue=None, splitchar=','):
        if defaultvalue is None:
            defaultvalue = []
        self._splitchar = splitchar
        TypedConfigObject.__init__(self, list, defaultvalue)

    def set(self, value):
        if isinstance(value, (str, unicode)):
            value = value.split(self._splitchar)
        self.value = value

class ConfigDict(dict):
    """ Dictionary that respects TypedConfigObjects when getting or
    setting.
    """
    def getitem(self, key):
        """ special method that is used in Configuration objects.
        Return the content of the TypedConfigObject wrapper, if it is
        present.
        """
        value = self[key]
        if isinstance(value, TypedConfigObject): value = value.value
        return value

    def __setitem__(self, key, value):
        """ TypedConfigObject instances get special treatment:
            If one would be overwritten, call its set() method instead.
            If the new value also is a TypedConfigObject, pass its value
            to set().
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
        """ Convenience overload. """
        for key, value in dict(newdict).iteritems(): self[key] = value

class Configuration(object):
    """ Container for several dictionaries representing configuration
    options from various sources:
    - The defaults, to be set from a Configurations.register_config call
    - The file config, read from all files given in a call to
      Configurations.register_files
    - The command line options, passed by a CLIConfig object through
      Configurations.set_cli_config
    It can be used from ConfigClient subclasses or instances to
    obtain the value to a config key, where the precedence is
    cli->files->defaults.
    Different section names can be used for groups of options from the
    register_config call, which correspond to the section names from the
    files.
    """
    def __init__(self, defaults):
        """ Initialize the dicts used to store the config and the list
        of section names that are added for defaults.
        """
        self.config_defaults  = ConfigDict()
        self.config_from_file = dict()
        self.config_from_cli  = ConfigDict()
        self.config           = ConfigDict()
        self.set_defaults(defaults)

    def __getitem__(self, key):
        """ Emulate read-only container behaviour. """
        if not self.config.has_key(key):
            raise NoSuchOptionError(key)
        return self.config.getitem(key)

    def __str__(self):
        return str(self.config)

    def has_key(self, key):
        """ Emulate read-only container behaviour. """
        return self.config.has_key(key)

    @property
    def info(self):
        """ Return the contents of all sources. """
        s = 'Defaults: %s\nCLI: %s\nFiles: %s' % (str(self.config_defaults),
                                                  str(self.config_from_cli),
                                                  str(self.config_from_file))
        return s

    def __rebuild_config(self):
        """ Collect the config options from the defaults, the file
        config sections that have been default-added and the cli
        config in that order and store them in self.config.
        The defaults and file config sections are iterated in the 
        order of the additions of the defaults.
        To be called after new values are added.
        """
        self.config = ConfigDict()
        self.config.update(self.config_defaults)
        self.config.update(self.config_from_file)
        self.config.update(self.config_from_cli)

    def set_defaults(self, new_defaults):
        """ Add a new unique section with default values to the list of
        default options.
        """
        self.config_defaults.update(new_defaults)
        self.__rebuild_config()

    def set_cli_config(self, values):
        """ Set the config values read from command line invocation.
            @param values: Obtained from an instance of OptionParser.
            Its __dict__ contains all of the possible command line 
            options. If an option hasn't been supplied, it is None, and
            thus not considered here.
            @type values: optparse.Values
        """
        self.config_from_cli.update([key, value] for key, value in 
                                    values.__dict__.iteritems() 
                                    if value is not None and
                                    self.config_defaults.has_key(key))
        self.__rebuild_config()

    def set_file_config(self, file_config):
        """ Add the values obtained from the files as a ConfigDict
        object and rebuild the main config.
        """
        self.config_from_file = ConfigDict()
        self.config_from_file.update(file_config)
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
        """ Return True if a section with name has been added. """
        return name in self.sections

class ConfigClientBase(object):
    """ A class which allows remote access to a Configuration. """
    def _init(self, name):
        """ Must be called from subclasses. """
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
        Configuration is ready.
        Mark as connected, so that the config isn't switched.
        """
        if not self.connected:
            self._config = config
            self.connected = True

class ConfigClient(ConfigClientBase):
    """ Standard read-only proxy for a Configuration. """
    def __init__(self, name):
        """ Connect to the Configuration called name.
        
        """
        super(ConfigClient, self)._init(name)

    def config(self, key):
        """ Obtain a config option's value. """
        if not self.connected: 
            raise ConfigClientNotYetConnectedError(self.name, key)
        return self._config[key]

    def __call__(self, key):
        return self.config(key)

    def print_all(self):
        print self._config.info

class CLIConfig(object):
    """ Proxy for setting the command line arguments as config values.
    
    """
    def __init__(self, values=None):
        self.set_cli_config(values)
    
    def set_cli_config(self, values):
        """ If present, set the values attribute and transfer them.
        
        """
        if values is not None:
            assert(isinstance(values, Values))
            self.values = values
            Configurations.set_cli_config(self.values)

class ConfigurationFactory(object):
    """ Construct Configuration objects out of a section of the given
    config files.
    """
    def __init__(self, files):
        self.files = files
        self.read_config()

    def read_config(self):
        self.config_parser = SafeConfigParser()
        self.config_parser.read(self.files)

    def create(self, section, defaults):
        config = Configuration(defaults)
        try:
            file_config = dict(self.config_parser.items(section))
            config.set_file_config(file_config)
        except NoSectionError, e: 
            logger.debug('ConfigParser: ' + str(e))
        return config

class Configurations(object):
    """ Program-wide register of Configuration instances.
    Connects the clients to the according Configuration, as soon as it
    has registered.
    """
    # A dict of configuration factories by an alias name
    _factories = { }
    # A dict of Configuration instances by their section name
    _configs = { }
    _cli_config = None
    # A mapping of config keys to -x cli short option characters
    _cli_short_options = { }
    _cli_params = { }
    # A dict of lists of client instances grouped by the name of the
    # target Configuration's name
    _pending_clients = { }

    @classmethod
    def register_files(cls, alias, *files):
        if not cls._factories.has_key(alias):
            cls._factories[alias] = ConfigurationFactory(files)

    @classmethod
    def register_config(cls, file_alias, section, **defaults):
        """ Add a Configuration instance to the configs dict that
        contains the specified section of the files denoted by the
        specified alias and connect waiting client instances.
        """
        if not cls._configs.has_key(section):
            config = cls._factories[file_alias].create(section, defaults)
            if cls._cli_config:
                config.set_cli_config(cls._cli_config)
            cls._configs[section] = config
            cls.notify_clients(section)

    @classmethod
    def set_cli_config(cls, values):
        cls._cli_config = values
        for config in cls._configs.values():
            config.set_cli_config(values)
        cls.notify_all_clients()

    @classmethod
    def register_client(cls, client):
        """ Connect a client instance to the according Configuration
        instance, buffering the request if neccessary.
        """
        try: 
            client.connect(cls._configs[client.name])
        except KeyError:
            if not cls._pending_clients.has_key(client.name):
                cls._pending_clients[client.name] = [ ]
            cls._pending_clients[client.name].append(client)

    @classmethod
    def notify_all_clients(cls):
        for name in cls._pending_clients.keys():
            cls.notify_clients(name)

    @classmethod
    def notify_clients(cls, name):
        """ Connects clients to Configuration 'name' that have been
        registered before their target and clear the client dict item.

        """
        if cls._configs.has_key(name):
            if cls._pending_clients.has_key(name):
                for client in cls._pending_clients[name]: 
                    client.connect(cls._configs[name])
                del cls._pending_clients[name]
        else:
            logger.debug('Configurations.notify clients called for'
                         ' Configuration \'%s\' which hasn\'t been added yet' %
                         name)

    @classmethod
    def override(self, section, **defaults):
        if self._configs.has_key(section):
            self._configs[section].set_defaults(defaults)
        else:
            logger.debug('Tried to override defaults in nonexistent section %s'
                         % section)

    @classmethod
    def parse_cli(self, positional=None):
        from argparse import ArgumentParser
        parser = ArgumentParser()
        arg = ['']
        params = {}
        if positional is not None:
            parser.add_argument(positional[0], nargs=positional[1])
        def add():
            parser.add_argument(*arg, **params)
        for config in self._configs.itervalues():
            for name, value in config.config.iteritems():
                if positional is None or name != positional[0]:
                    arg = ['--%s' % name]
                    params = {'default': None}
                    if self._cli_short_options.has_key(name):
                        arg.append('-%s' % self._cli_short_options[name])
                    if self._cli_params.has_key(name):
                        params.update(self._cli_params[name])
                    if isinstance(value, BoolConfigObject):
                        params['action'] = 'store_true'
                        add()
                        params = {'default': None}
                        arg = ['--no-%s' % name]
                        params['action'] = 'store_false'
                        params['dest'] = name
                    add()
        self.set_cli_config(parser.parse_args())

    @classmethod
    def set_cli_short_options(self, **options):
        self._cli_short_options.update(options)

    @classmethod
    def set_cli_params(self, name, *short, **params):
        if short:
            self.set_cli_short_options(dict([[name, short[0]]]))
        self._cli_params[name] = params

    @classmethod
    def clear(self):
        self._configs = {}
        self._cli_config = None
        self._pending_clients = {}
        self._factories = {}
