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

from unittest import TestCase

from tek.config import Configurations, lazy_configurable, ListConfigOption

class ConfigTest(TestCase):
    def test_lazy_configurable(self):
        Configurations.clear()
        Configurations.register_files('test')
        Configurations.register_config('test', 'sec1', key1='val1',
                                       key2=ListConfigOption(['asdf', 'jkl;']))
        Configurations.register_config('test', 'sec2', key3='val3')
        @lazy_configurable(sec1=['key1', 'key2'], sec2=['key3'])
        class Lazy(object):
            pass
        lazy = Lazy()
        self.assertEqual(lazy._key1, 'val1')
        self.assertEqual(lazy._sec1__key2, ['asdf', 'jkl;'])
        self.assertEqual(lazy._key3, 'val3')
        self.assertRaises(AttributeError, lambda: lazy._noattr)
