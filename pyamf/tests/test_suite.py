# Copyright (c) The PyAMF Project.
# See LICENSE.txt for details.

"""
Tests for the project test suite entry point.
"""

import ast
import os.path
import unittest

import pyamf.tests


def iter_test_ids(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            for test_id in iter_test_ids(item):
                yield test_id
        else:
            yield item.id()


class SupportedPythonVersionsTestCase(unittest.TestCase):
    def get_setup_classifiers(self):
        root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        setup_py = os.path.join(root, 'setup.py')

        with open(setup_py, 'r') as fp:
            tree = ast.parse(fp.read(), setup_py)

        for node in tree.body:
            if not isinstance(node, ast.Assign):
                continue

            for target in node.targets:
                if getattr(target, 'id', None) == 'classifiers':
                    return ast.literal_eval(node.value)

        self.fail('setup.py does not define classifiers')

    def test_supported_versions(self):
        self.assertEqual(
            pyamf.tests.SUPPORTED_PYTHON_VERSIONS,
            ((3, 11), (3, 12), (3, 13), (3, 14))
        )

    def test_setup_classifiers_match_supported_versions(self):
        supported = [
            'Programming Language :: Python :: %d.%d' % version
            for version in pyamf.tests.SUPPORTED_PYTHON_VERSIONS
        ]
        classifiers = [
            classifier.strip()
            for classifier in self.get_setup_classifiers().strip().split('\n')
            if classifier.strip().startswith(
                'Programming Language :: Python :: 3.'
            )
        ]

        self.assertEqual(classifiers, supported)


class DefaultSuiteTestCase(unittest.TestCase):
    unsupported_modules = (
        'pyamf.tests.gateway.test_django',
        'pyamf.tests.gateway.test_google',
        'pyamf.tests.gateway.test_twisted',
        'pyamf.adapters.tests.google',
        'pyamf.adapters.tests.test_django',
        'pyamf.adapters.tests.test_elixir',
        'pyamf.adapters.tests.test_sqlalchemy',
    )
    unsupported_test_prefixes = (
        'pyamf.tests.test_basic.TestAMF0Codecs.',
        'pyamf.tests.test_basic.TestAMF3Codecs.',
    )

    def test_default_suite_excludes_unsupported_integrations(self):
        test_ids = list(iter_test_ids(pyamf.tests.get_suite()))

        for module in self.unsupported_modules:
            self.assertFalse(
                any(test_id.startswith(module) for test_id in test_ids),
                '%s should not be included in the default suite' % (module,)
            )

    def test_default_suite_excludes_extension_tests(self):
        test_ids = list(iter_test_ids(pyamf.tests.get_suite()))

        for prefix in self.unsupported_test_prefixes:
            self.assertFalse(
                any(test_id.startswith(prefix) for test_id in test_ids),
                '%s should not be included in the default suite' % (prefix,)
            )

    def test_default_suite_keeps_wsgi_gateway(self):
        test_ids = list(iter_test_ids(pyamf.tests.get_suite()))

        self.assertTrue(
            any(
                test_id.startswith('pyamf.tests.gateway.test_wsgi')
                for test_id in test_ids
            )
        )
