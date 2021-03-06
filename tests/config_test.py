import sys
import sure  # NOQA

from tek.test import Spec, fixture_path, temp_file
from tek.config import (Config, configurable, ConfigClient, NoSuchSectionError,
                        NoSuchOptionError)
from tek.config.options import (ListConfigOption, FileSizeConfigOption,
                                DictConfigOption)
from tek.config.write import write_pkg_config


class Config_(Spec):

    def configurable(self):
        Config.clear()
        Config.register_config('test', 'sec1', key1='val1',
                                       key2=ListConfigOption(['asdf', 'jkl;']))
        Config.register_config('test', 'sec2', key3='val3')

        @configurable(sec1=['key1', 'key2'], sec2=['key3'])
        class Lazy(object):
            pass
        lazy = Lazy()
        lazy._key1.should.equal('val1')
        lazy._sec1__key2.should.equal(['asdf', 'jkl;'])
        lazy._key3.should.equal('val3')
        noattr = lambda: lazy._noattr
        noattr.should.throw(AttributeError)

    def file_size(self):
        Config.clear()
        Config.register_config('test', 'sec1',
                                       key1=FileSizeConfigOption('5.54G'))
        conf = ConfigClient('sec1')
        conf('key1').should.equal(5540000000)

    def dict(self):
        class MyClass(object):

            def __init__(self, arg):
                self._arg = arg

            def __eq__(self, other):
                return self._arg == other._arg

        Config.clear()
        value = DictConfigOption('1:foo,2:boo', key_type=int,
                                 dictvalue_type=MyClass)
        Config.register_config('test', 'sec1', key1=value)
        conf = ConfigClient('sec1')
        conf('key1').should.equal({1: MyClass('foo'), 2: MyClass('boo')})
        conf('key1').should_not.equal({1: MyClass('afoo'), 2: MyClass('boo')})

    def dict_escape(self):
        Config.clear()
        value = DictConfigOption('a\:b:foo\:moo,a\,b:boo\,zoo')
        Config.register_config('test', 'sec1', key1=value)
        conf = ConfigClient('sec1')
        conf('key1').should.equal({'a:b': 'foo:moo', 'a,b': 'boo,zoo'})

    def autoload(self):
        Config.allow_files = True
        sys.path.insert(0, fixture_path('config'))
        Config.setup('mod1', 'mod3')
        Config['sec1'].key1.should.equal('success')
        Config['sec2'].key1.should.equal('val1')
        invalid_section = lambda: Config['sec9']
        invalid_section.when.called_with().should.throw(NoSuchSectionError)
        invalid_option = lambda: Config['sec1'].inval
        invalid_option.when.called_with().should.throw(NoSuchOptionError)

    def write(self):
        outfile = temp_file('config', 'outfile.conf')
        write_pkg_config(fixture_path('config'), outfile, 'mod2')
        with open(outfile) as _file:
            lines = _file.readlines()
            lines.should.equal(['[sec2]\n', '# key1 = val0\n', '\n'])

    def cli(self):
        from tests._fixtures.config.mod1.sub.cli import cli_test
        data = []
        cli_test(data=data)
        data[-1].should.equal('val1')

__all__ = []
