__copyright__ = """ Copyright (c) 2009-2011 Torsten Schmits

This file is part of mootils. mootils is free software;
you can redistribute it and/or modify it under the terms of the GNU General
Public License version 2, as published by the Free Software Foundation.

mootils is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
details.

You should have received a copy of the GNU General Public License along with
this program; if not, write to the Free Software Foundation, Inc., 59 Temple
Place, Suite 330, Boston, MA  02111-1307  USA

"""

import re, ConfigParser

from tek.config.errors import *
from tek.config.options import *
from tek.config.options import ConfigOption, TypedConfigOption
from tek import logger, debug

__all__ = ['ConfigError', 'ConfigClient', 'Configurations', 'configurable',
           'lazy_configurable']

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
        if isinstance(value, TypedConfigOption):
            value = value.effective_value
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
                    self[key].set_from_co(value)
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
        logger.info(self._config.info)

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
        self.config_parser = ConfigParser.SafeConfigParser()
        self.config_parser.read(self.files)

    def create(self, section, defaults):
        config = Configuration(defaults)
        if self._allow_files:
            try:
                file_config = dict(self.config_parser.items(section))
                config.set_file_config(file_config)
            except ConfigParser.NoSectionError as e:
                logger.debug('ConfigParser: ' + str(e))
            except ConfigParser.Error as e:
                logger.error('ConfigParser: ' + str(e))
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
    allow_override = True
    enable_lazy_class_attr = True

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
        if self.allow_override:
            if self._configs.has_key(section):
                self._configs[section].set_defaults(defaults)
            else:
                logger.debug('Tried to override defaults in nonexistent section'
                             ' %s' % section)

    @classmethod
    def override(self, section, **values):
        if self.allow_override:
            if self._configs.has_key(section):
                self._configs[section].override(**values)
            else:
                logger.debug('Tried to override values in nonexistent section'
                             ' %s' % section)

    @classmethod
    def parse_cli(self, positional=None):
        from argparse import ArgumentParser
        parser = ArgumentParser()
        arg = ['']
        params = {}
        seen = []
        if positional is not None:
            parser.add_argument(positional[0], nargs=positional[1])
        def add():
            parser.add_argument(*arg, **params)
        for config in self._configs.itervalues():
            for name, value in config.config.iteritems():
                if name in seen:
                    continue
                seen.append(name)
                switchname = name.replace('_', '-')
                if (not (isinstance(value, ConfigOption) and value.positional)
                    and (positional is None or name != positional[0])):
                    arg = ['--%s' % switchname]
                    params = {'default': None}
                    if self._cli_short_options.has_key(name):
                        arg.append('-%s' % self._cli_short_options[name])
                    if self._cli_params.has_key(name):
                        params.update(self._cli_params[name])
                    if isinstance(value, ConfigOption):
                        params.update(value.argparse_params)
                        if value.short:
                            arg.append('-%s' % value.short)
                    if isinstance(value, BoolConfigOption):
                        params['action'] = 'store_true'
                        if value.no:
                            add()
                            params = {'default': None}
                            arg = ['--no-%s' % switchname]
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
        for cls in self._configurables:
            if hasattr(cls, '__conf_init__'):
                cls.__init__ = cls.__conf_init__

    @classmethod
    def add_configurable(self, cls):
        self._configurables.add(cls)

    @classmethod
    def write_config(self, filename):
        def write_section(f, section, config):
            f.write('[{0}]\n'.format(section))
            for key, value in config.config.iteritems():
                if not (isinstance(value, ConfigOption) and value.positional):
                    if isinstance(value, ConfigOption) and value.help:
                        f.write('\n# {0}\n'.format(value.help))
                    f.write('# {0} = {1:s}\n'.format(key, value))
            f.write('\n')
        with open(filename, 'w') as f:
            if self._configs.has_key('global'):
                write_section(f, 'global', self._configs['global'])
            for section, config in self._configs.iteritems():
                if not section == 'global':
                    write_section(f, section, config)

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

conf_attr_re = re.compile(r'_((?P<section>.+)__)?(?P<key>.+)')

def lazy_configurable(set_class_attr=True, **sections):
    """ Same class decorator as configurable, with the difference that
    config values are not set until first accessed. This is done by
    overriding __getattr__ and setting matching attributes from the
    config.
    """
    def dec(c):
        def conf_getattr(self, attr):
            def try_section(name):
                section = sections[name]
                if key in section:
                    target = (c if set_class_attr and
                              Configurations.enable_lazy_class_attr else self)
                    setattr(target, attr, ConfigClient(name)(key))
                    return True
            match = conf_attr_re.match(attr)
            if match:
                section, key = match.group('section'), match.group('key')
                sections_to_try = ([section] if section in sections else
                                   sections)
                for section in sections_to_try:
                    if try_section(section):
                        return getattr(self, attr)
            return c.__orig_getattr__(self, attr)
        def noattr(self, attr):
            t = self.__class__.__name__
            error = "type object '{0}' has no attribute '{1}'".format(t, attr)
            raise AttributeError(error)
        Configurations.add_configurable(c)
        c.__orig_getattr__ = getattr(c, '__getattr__', noattr)
        c.__conf_getattr__ = c.__getattr__ = conf_getattr
        return c
    return dec
