from __future__ import absolute_import
from ConfigParser import SafeConfigParser, NoSectionError
from optparse import Values

from tek.config.errors import *
from tek import logger, debug

__all__ = ['ConfigError', 'ConfigClient', 'Configurations', 'configurable']

def boolify(value):
    """ Return a string's boolean value if it is a string and "true" or
    "false"(case insensitive), else just return the object.
    """
    try:
        return value.lower() == 'true'
    except:
        return bool(value)

class ConfigOption(object):
    def __init__(self, **params):
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

class BoolConfigOption(TypedConfigOption):
    """ Specialization of TypedConfigOption for booleans, as they must
    be parsed from strings differently.
    """
    def __init__(self, defaultvalue=False, **params):
        """ Set the value_type to bool. """
        TypedConfigOption.__init__(self, bool, defaultvalue, **params)

    def set(self, arg):
        """ Transform arg into a bool value and pass it to super. """
        super(BoolConfigOption, self).set(boolify(arg))

class ListConfigOption(TypedConfigOption):
    def __init__(self, defaultvalue=None, splitchar=',', **params):
        if defaultvalue is None:
            defaultvalue = []
        self._splitchar = splitchar
        TypedConfigOption.__init__(self, list, defaultvalue, **params)

    def set(self, value):
        if isinstance(value, basestring):
            value = value.split(self._splitchar)
        self.value = value

    def __str__(self):
        return self._splitchar.join(self.value)

class UnicodeConfigOption(TypedConfigOption):
    def __init__(self, default, **params):
        TypedConfigOption.__init__(self, unicode, default, **params)

    def __str__(self):
        return self.value.encode('utf-8')

class ConfigDict(dict):
    """ Dictionary that respects TypedConfigOptions when getting or
    setting.
    """
    def getitem(self, key):
        """ special method that is used in Configuration objects.
        Return the content of the TypedConfigOption wrapper, if it is
        present.
        """
        value = self[key]
        if isinstance(value, TypedConfigOption): value = value.value
        return value

    def __setitem__(self, key, value):
        """ TypedConfigOption instances get special treatment:
            If one would be overwritten, call its set() method instead.
            If the new value also is a TypedConfigOption, pass its value
            to set().
            If the key is new, try to create a TypedConfigOption.
        """
        if not self.has_key(key):
            if not (isinstance(value, basestring) or
                    isinstance(value, TypedConfigOption) or
                    value is None):
                if isinstance(value, bool):
                    value = BoolConfigOption(value)
                else:
                    value = TypedConfigOption(type(value), value)
            dict.__setitem__(self, key, value)
        else:
            if isinstance(self[key], TypedConfigOption):
                if isinstance(value, TypedConfigOption):
                    self[key].set(value.value)
                    self[key].set_argparse_params(value.argparse_params)
                else:
                    self[key].set(value)
            else:
                dict.__setitem__(self, key, value)

    def update(self, newdict):
        """ Convenience overload. """
        for key, value in dict(newdict).iteritems():
            self[key] = value

class Configuration(object):
    """ Container for several dictionaries representing configuration
    options from various sources:
    - The defaults, to be set from a Configurations.register_config call
    - The file config, read from all files given in a call to
      Configurations.register_files
    - The command line options, passed by a CLIConfig object through
      Configurations.set_cli_config
    - Values set by Configurations.override, mainly for testing purposes
    It can be used from ConfigClient subclasses or instances to
    obtain the value to a config key, where the precedence is
    overridden->cli->files->defaults.
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
        self.overridden       = ConfigDict()
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
        self.config.update(self.overridden)

    def config_update(f):
        def wrap(self, *a, **kw):
            f(self, *a, **kw)
            self.__rebuild_config()
        return wrap

    @config_update
    def set_defaults(self, new_defaults):
        """ Add a new unique section with default values to the list of
        default options.
        """
        self.config_defaults.update(new_defaults)

    @config_update
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

    @config_update
    def set_file_config(self, file_config):
        """ Add the values obtained from the files as a ConfigDict
        object and rebuild the main config.
        """
        self.config_from_file = ConfigDict()
        self.config_from_file.update(file_config)

    @config_update
    def override(self, **values):
        self.overridden.update(values)

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

class ConfigClient(object):
    """ Standard read-only proxy for a Configuration. """
    def __init__(self, name):
        """ Connect to the Configuration called name. """
        self.connected = False
        self._config = None
        self.__register(name)

    def __register(self, name):
        """ Add self to the list of instances waiting for the 
        Configuration in the Configurations proxy.
        """
        self.name = name
        Configurations.register_client(self)

    def config(self, key):
        """ Obtain a config option's value. """
        if self._config is None:
            raise ConfigClientNotYetConnectedError(self.name, key)
        return self._config[key]

    def __call__(self, key):
        return self.config(key)

    def print_all(self):
        debug(self._config.info)

    def connect(self, config):
        """ Reference the Configuration instance as the config to be
        used by the client. Called from Configurations once the 
        Configuration is ready.
        Mark as connected, so that the config isn't switched.
        """
        if self._config is None:
            self._config = config

class ConfigurationFactory(object):
    """ Construct Configuration objects out of a section of the given
    config files.
    """
    def __init__(self, files, allow_files=True):
        self.files = files
        self._allow_files = allow_files
        self.read_config()

    def read_config(self):
        self.config_parser = SafeConfigParser()
        self.config_parser.read(self.files)

    def create(self, section, defaults):
        config = Configuration(defaults)
        if self._allow_files:
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
    _factories = {}
    # A dict of Configuration instances by their section name
    _configs = {}
    _cli_config = None
    # A mapping of config keys to -x cli short option characters
    _cli_short_options = {}
    _cli_params = {}
    # A dict of lists of client instances grouped by the name of the
    # target Configuration's name
    _pending_clients = {}
    # classes that have attributes set from configurable decorator
    _configurables = set()
    # read config from file system
    allow_files = True

    @classmethod
    def register_files(cls, alias, *files):
        if not cls._factories.has_key(alias):
            cls._factories[alias] = ConfigurationFactory(files, cls.allow_files)

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
        else:
            cls._configs[section].set_defaults(defaults)

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
    def override_defaults(self, section, **defaults):
        if self._configs.has_key(section):
            self._configs[section].set_defaults(defaults)
        else:
            logger.debug('Tried to override defaults in nonexistent section %s'
                         % section)

    @classmethod
    def override(self, section, **values):
        if self._configs.has_key(section):
            self._configs[section].override(**values)
        else:
            logger.debug('Tried to override values in nonexistent section %s'
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
                    if isinstance(value, BoolConfigOption):
                        params['action'] = 'store_true'
                        add()
                        params = {'default': None}
                        arg = ['--no-%s' % name]
                        params['action'] = 'store_false'
                        params['dest'] = name
                    if isinstance(value, ConfigOption):
                        params.update(value.argparse_params)
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
        for cls in self._configurables:
            if hasattr(cls, '__conf_init__'):
                cls.__init__ = cls.__conf_init__

    @classmethod
    def add_configurable(self, cls):
        self._configurables.add(cls)

    @classmethod
    def write_config(self, filename):
        with open(filename, 'w') as f:
            for section, config in self._configs.iteritems():
                f.write('[{0}]\n'.format(section))
                for key, value in config.config.iteritems():
                    if isinstance(value, ConfigOption) and value.help:
                        f.write('# {0}\n'.format(value.help))
                    f.write('# {0} = {1:s}\n'.format(key, value))
                f.write('\n')

def configurable(prefix=False, **sections):
    """ Class decorator, to be called with keyword arguments each
    describing a config section and corresponding keys. The first time
    the class is being instantiated, the config keys and their values
    are being set as attributes to the class, thus ensuring that the cli
    config may have been processed.  If prefix is True, each key is
    prefixed with its section name. All attributes get a leading '_'.
    The attribute '__conf_init__' is used to save the conf setter.
    This is only neccessary to allow the config to be reread using
    Configurations.clear(), e.g. in test cases.
    """
    def dec(c):
        def set_conf(*a, **kw):
            for section, keys in sections.iteritems():
                conf = ConfigClient(section)
                for k in keys:
                    attrname = '_{0}'.format(k)
                    if prefix:
                        attrname = '_{0}{1}'.format(section, attrname)
                    setattr(c, attrname, conf(k))
            c.__init__ = c.__orig_init__
            c.__init__(*a, **kw)
        Configurations.add_configurable(c)
        c.__orig_init__ = c.__init__
        c.__conf_init__ = c.__init__ = set_conf
        return c
    return dec
