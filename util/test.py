__copyright__ = """ Copyright (c) 2010 Torsten Schmits

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

import re, unittest

from tek import debug, logger
from tek.util.module import submodules

__all__ = ['run_all_tests', 'test_suite_all']

test_loader = unittest.defaultTestLoader.loadTestsFromModule

def test_cases(pkg_name, include_tests={}, exclude_tests={}):
    for test_mod in submodules(pkg_name):
        for suite in test_loader(test_mod)._tests:
            for test in suite._tests:
                cname = test.__class__.__name__
                mname = test._testMethodName
                cmname = '{0}.{1}'.format(cname, mname)
                if not ((include_tests and
                     (not include_tests.has_key(cname) or
                      not mname in include_tests[cname]))
                or (exclude_tests.has_key(cname) and
                    (not exclude_tests[cname] or
                     (mname in exclude_tests[cname])))):
                    yield test

def test_suite_all(pkg_name, **kw):
    cases = test_cases(pkg_name, **kw)
    return unittest.TestSuite(cases)

def run_all_tests(pkg_name, **kw):
    suite = test_suite_all(pkg_name, **kw)
    unittest.TextTestRunner().run(suite)
