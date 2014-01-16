
import unittest

from tek import Configurations
from tek.util.module import submodules

__all__ = ['run_all_tests', 'test_suite_all']

# Lazy attributes can't be cleared on reset
Configurations.enable_lazy_class_attr = False

test_loader = unittest.defaultTestLoader.loadTestsFromModule

def test_cases(pkg_name, include_tests={}, exclude_tests={}):
    for test_mod in submodules(pkg_name):
        for suite in test_loader(test_mod)._tests:
            for test in suite._tests:
                cname = test.__class__.__name__
                mname = test._testMethodName
                if not ((include_tests and
                         (cname not in include_tests or
                          (include_tests[cname] and
                           not mname in include_tests[cname])))
                or (cname in exclude_tests and
                    (not exclude_tests[cname] or
                     (mname in exclude_tests[cname])))):
                    yield test

def test_suite_all(pkg_name, **kw):
    cases = test_cases(pkg_name, **kw)
    return unittest.TestSuite(cases)

def run_all_tests(pkg_name, **kw):
    suite = test_suite_all(pkg_name, **kw)
    unittest.TextTestRunner().run(suite)
