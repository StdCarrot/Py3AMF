# Copyright (c) The PyAMF Project.
# See LICENSE.txt for details.

"""
Unit tests.

@since: 0.1.0
"""

try:
    import unittest2 as unittest
    import sys

    sys.modules['unittest'] = unittest
except ImportError:
    import unittest


SUPPORTED_PYTHON_VERSIONS = ((3, 11), (3, 12), (3, 13), (3, 14))

DEFAULT_TEST_MODULES = (
    'pyamf.tests.test_adapters',
    'pyamf.tests.test_adapters_util',
    'pyamf.tests.test_alias',
    'pyamf.tests.test_amf0',
    'pyamf.tests.test_amf3',
    'pyamf.tests.test_basic',
    'pyamf.tests.test_codec',
    'pyamf.tests.test_flex',
    'pyamf.tests.test_flex_messaging',
    'pyamf.tests.test_gateway',
    'pyamf.tests.test_imports',
    'pyamf.tests.test_remoting',
    'pyamf.tests.test_sol',
    'pyamf.tests.test_suite',
    'pyamf.tests.test_util',
    'pyamf.tests.test_versions',
    'pyamf.tests.test_xml',
    'pyamf.tests.gateway.test_wsgi',
    'pyamf.tests.modules.test_decimal',
    'pyamf.tests.modules.test_sets',
    'pyamf.tests.remoting.test_amf0',
    'pyamf.tests.remoting.test_client',
    'pyamf.tests.remoting.test_remoteobject',
    'pyamf.adapters.tests.test_array',
    'pyamf.adapters.tests.test_collections',
    'pyamf.adapters.tests.test_weakref',
)

EXCLUDED_TEST_PREFIXES = (
    'pyamf.tests.test_basic.TestAMF0Codecs.',
    'pyamf.tests.test_basic.TestAMF3Codecs.',
)


if not hasattr(unittest.TestCase, 'assertIdentical'):
    def assertIdentical(self, first, second, msg=None):
        """
        Fail the test if C{first} is not C{second}.  This is an
        obect-identity-equality test, not an object equality (i.e. C{__eq__})
        test.

        @param msg: if msg is None, then the failure message will be
            '%r is not %r' % (first, second)
        """
        if first is not second:
            raise AssertionError(msg or '%r is not %r' % (first, second))

        return first

    unittest.TestCase.assertIdentical = assertIdentical

if not hasattr(unittest.TestCase, 'assertNotIdentical'):
    def assertNotIdentical(self, first, second, msg=None):
        """
        Fail the test if C{first} is C{second}.  This is an
        object-identity-equality test, not an object equality
        (i.e. C{__eq__}) test.

        @param msg: if msg is None, then the failure message will be
            '%r is %r' % (first, second)
        """
        if first is second:
            raise AssertionError(msg or '%r is %r' % (first, second))

        return first

    unittest.TestCase.assertNotIdentical = assertNotIdentical

if not hasattr(unittest.TestCase, 'patch'):
    import inspect

    def unpatch(self):
        for orig, part, replaced in self.__patches:
            setattr(orig, part, replaced)

    def patch(self, orig, replace):
        if not hasattr(self, '__patches'):
            self.__patches = []
            self.addCleanup(unpatch, self)

        f = inspect.stack()[1][0]

        parts = orig.split('.')

        v = f.f_globals.copy()
        v.update(f.f_locals)

        orig = v[parts[0]]

        for part in parts[1:-1]:
            orig = getattr(orig, part)

        to_replace = getattr(orig, parts[-1])

        self.__patches.append((orig, parts[-1], to_replace))

        setattr(orig, parts[-1], replace)

    unittest.TestCase.patch = patch


def _filter_suite(suite):
    filtered = unittest.TestSuite()

    for item in suite:
        if isinstance(item, unittest.TestSuite):
            child = _filter_suite(item)

            if child.countTestCases():
                filtered.addTest(child)
        elif not _exclude_test(item):
            filtered.addTest(item)

    return filtered


def _exclude_test(test):
    test_id = test.id()

    for prefix in EXCLUDED_TEST_PREFIXES:
        if test_id.startswith(prefix):
            return True

    return False


def get_suite():
    """
    Return the default supported test suite.
    """
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    for module in DEFAULT_TEST_MODULES:
        suite.addTest(loader.loadTestsFromName(module))

    return _filter_suite(suite)


def main():
    """
    Run all of the tests when run as a module with -m.
    """
    runner = unittest.TextTestRunner()
    runner.run(get_suite())


if __name__ == '__main__':
    main()
