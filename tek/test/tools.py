__copyright__ = """ Copyright (c) 2012-2013 Torsten Schmits

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

import unittest

from tek.tools import sizeof_fmt

class ToolsTest(unittest.TestCase):
    def test_sizeof_fmt(self):
        self.assertEqual(sizeof_fmt(1450000, prec=3, bi=False), '1.450 MB')
        self.assertEqual(sizeof_fmt(1450000, bi=True), '1.4 MB')

if __name__ == '__main__':
    unittest.main()
