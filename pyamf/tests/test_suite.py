# Copyright (c) The PyAMF Project.
# See LICENSE.txt for details.

"""
Tests for the project test suite entry point.
"""

import ast
import importlib.util
import os.path
import subprocess
import sys
import textwrap
import tomllib
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
    unsupported_classifiers = (
        'Framework :: Django',
        'Framework :: Pylons',
        'Framework :: Twisted',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: C',
        'Programming Language :: Cython',
    )
    deprecated_setup_keywords = (
        'test_suite',
        'tests_require',
    )

    def get_source_root(self):
        root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

        if not os.path.exists(os.path.join(root, 'setup.py')):
            self.skipTest('source checkout metadata is not installed')

        return root

    def get_setup_classifiers(self):
        root = self.get_source_root()
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

    def get_setup_version(self):
        root = self.get_source_root()
        setup_py = os.path.join(root, 'setup.py')

        with open(setup_py, 'r') as fp:
            tree = ast.parse(fp.read(), setup_py)

        for node in tree.body:
            if not isinstance(node, ast.Assign):
                continue

            for target in node.targets:
                if getattr(target, 'id', None) == 'version':
                    return ast.literal_eval(node.value)

        self.fail('setup.py does not define version')

    def get_setup_call_keywords(self):
        root = self.get_source_root()
        setup_py = os.path.join(root, 'setup.py')

        with open(setup_py, 'r') as fp:
            tree = ast.parse(fp.read(), setup_py)

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue

            if getattr(node.func, 'id', None) == 'setup':
                return {
                    keyword.arg
                    for keyword in node.keywords
                    if keyword.arg is not None
                }

        self.fail('setup.py does not call setup')

    def get_setup_extras(self):
        root = self.get_source_root()
        setupinfo_py = os.path.join(root, 'setupinfo.py')

        with open(setupinfo_py, 'r') as fp:
            tree = ast.parse(fp.read(), setupinfo_py)

        for node in tree.body:
            if not isinstance(node, ast.FunctionDef):
                continue

            if node.name != 'get_extras_require':
                continue

            for item in node.body:
                if isinstance(item, ast.Return):
                    return ast.literal_eval(item.value)

        self.fail('setupinfo.py does not define get_extras_require')

    def get_build_backend(self):
        root = self.get_source_root()
        backend_py = os.path.join(root, 'py3amf_build_backend.py')

        if not os.path.exists(backend_py):
            self.fail('py3amf_build_backend.py does not exist')

        spec = importlib.util.spec_from_file_location(
            'py3amf_build_backend', backend_py)
        backend = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(backend)

        return backend

    def get_setupinfo(self):
        root = self.get_source_root()
        setupinfo_py = os.path.join(root, 'setupinfo.py')
        spec = importlib.util.spec_from_file_location('setupinfo', setupinfo_py)
        setupinfo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(setupinfo)

        return setupinfo

    def get_pyproject(self):
        root = self.get_source_root()

        with open(os.path.join(root, 'pyproject.toml'), 'rb') as fp:
            return tomllib.load(fp)

    def test_setup_version(self):
        self.assertEqual(self.get_setup_version(), (0, 9, 0))

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

    def test_setup_classifiers_exclude_unsupported_surfaces(self):
        classifiers = set(
            classifier.strip()
            for classifier in self.get_setup_classifiers().strip().split('\n')
            if classifier.strip()
        )

        for classifier in self.unsupported_classifiers:
            self.assertNotIn(classifier, classifiers)

    def test_setup_excludes_deprecated_setuptools_test_keywords(self):
        setup_keywords = self.get_setup_call_keywords()

        for keyword in self.deprecated_setup_keywords:
            self.assertNotIn(keyword, setup_keywords)

    def test_setup_extras_exclude_unsupported_integrations(self):
        self.assertEqual(
            set(self.get_setup_extras()),
            set(['lxml'])
        )

    def test_setup_extensions_are_disabled_by_default(self):
        setupinfo = self.get_setupinfo()
        self.patch('setupinfo.can_compile_extensions', lambda: True)

        self.assertEqual(setupinfo.get_extensions(), [])

    def test_cython_build_is_disabled_without_config_setting(self):
        backend = self.get_build_backend()

        self.assertFalse(backend.cython_enabled(None))
        self.assertFalse(backend.cython_enabled({}))

        for value in (None, False, 0, '', '0', 'false', 'no', 'off',
                      ['0', 'false']):
            self.assertFalse(
                backend.cython_enabled({'py3amf.ext.cython': value}),
                repr(value))

    def test_cython_build_is_enabled_by_config_setting(self):
        backend = self.get_build_backend()

        for value in (True, 1, '1', ' true ', 'TRUE', 'yes', 'ON',
                      ['false', 'true']):
            self.assertTrue(
                backend.cython_enabled({'py3amf.ext.cython': value}),
                repr(value))

    def test_default_wheel_build_does_not_require_cython(self):
        backend = self.get_build_backend()
        self.assertTrue(hasattr(backend, 'get_requires_for_build_wheel'))
        self.patch(
            'backend._build_meta.get_requires_for_build_wheel',
            lambda config_settings: ['wheel'])

        requirements = backend.get_requires_for_build_wheel()

        self.assertEqual(requirements, ['wheel'])

    def test_cython_wheel_build_requires_cython(self):
        backend = self.get_build_backend()
        self.patch(
            'backend._build_meta.get_requires_for_build_wheel',
            lambda config_settings: ['wheel'])

        requirements = backend.get_requires_for_build_wheel({
            'py3amf.ext.cython': '1',
        })

        self.assertEqual(requirements, ['wheel', 'Cython'])

    def test_cython_wheel_build_enables_extensions_temporarily(self):
        backend = self.get_build_backend()
        self.assertTrue(hasattr(backend, 'build_wheel'))
        build_values = []

        def build_wheel(wheel_directory, config_settings,
                        metadata_directory):
            build_values.append(os.environ.get('PY3AMF_BUILD_CYTHON'))
            return 'Py3AMF.whl'

        self.patch('backend._build_meta.build_wheel', build_wheel)

        wheel = backend.build_wheel(
            'dist', {'py3amf.ext.cython': '1'})

        self.assertEqual(wheel, 'Py3AMF.whl')
        self.assertEqual(build_values, ['1'])
        self.assertNotIn('PY3AMF_BUILD_CYTHON', os.environ)

    def test_requested_cython_build_fails_when_unavailable(self):
        setupinfo = self.get_setupinfo()
        name = 'PY3AMF_BUILD_CYTHON'
        previous = os.environ.pop(name, None)
        os.environ[name] = '1'

        def restore_environment():
            os.environ.pop(name, None)

            if previous is not None:
                os.environ[name] = previous

        self.addCleanup(restore_environment)
        self.patch('setupinfo.can_compile_extensions', lambda: False)

        with self.assertRaisesRegex(
                RuntimeError, 'Cython extension build was requested'):
            setupinfo.get_extensions()

    def test_pyproject_uses_optional_cython_build_backend(self):
        build_system = self.get_pyproject()['build-system']

        self.assertNotIn('Cython', build_system['requires'])
        self.assertEqual(
            build_system['build-backend'], 'py3amf_build_backend')
        self.assertEqual(build_system['backend-path'], ['.'])

    def test_sdist_includes_build_backend(self):
        root = self.get_source_root()

        with open(os.path.join(root, 'MANIFEST.in'), 'r') as fp:
            manifest = fp.read().splitlines()

        self.assertIn('include py3amf_build_backend.py', manifest)

    def test_sdist_build_does_not_enable_extensions(self):
        backend = self.get_build_backend()
        self.assertTrue(hasattr(backend, 'build_sdist'))
        self.assertTrue(hasattr(backend, 'get_requires_for_build_sdist'))
        build_values = []

        def build_sdist(sdist_directory, config_settings):
            build_values.append(os.environ.get('PY3AMF_BUILD_CYTHON'))
            return 'Py3AMF.tar.gz'

        self.patch('backend._build_meta.build_sdist', build_sdist)
        self.patch(
            'backend._build_meta.get_requires_for_build_sdist',
            lambda config_settings: ['wheel'])

        requirements = backend.get_requires_for_build_sdist({
            'py3amf.ext.cython': '1',
        })
        sdist = backend.build_sdist(
            'dist', {'py3amf.ext.cython': '1'})

        self.assertEqual(requirements, ['wheel'])
        self.assertEqual(sdist, 'Py3AMF.tar.gz')
        self.assertEqual(build_values, [None])

    def test_cython_setting_applies_to_binary_build_hooks(self):
        backend = self.get_build_backend()
        hook_names = (
            'prepare_metadata_for_build_wheel',
            'get_requires_for_build_editable',
            'prepare_metadata_for_build_editable',
            'build_editable',
        )

        for hook_name in hook_names:
            self.assertTrue(hasattr(backend, hook_name), hook_name)

        build_values = []

        def record_environment(*args):
            build_values.append(os.environ.get('PY3AMF_BUILD_CYTHON'))
            return 'result'

        self.patch(
            'backend._build_meta.prepare_metadata_for_build_wheel',
            record_environment)
        self.patch(
            'backend._build_meta.get_requires_for_build_editable',
            lambda config_settings: ['wheel'])
        self.patch(
            'backend._build_meta.prepare_metadata_for_build_editable',
            record_environment)
        self.patch(
            'backend._build_meta.build_editable', record_environment)
        config_settings = {'py3amf.ext.cython': '1'}

        requirements = backend.get_requires_for_build_editable(
            config_settings)
        backend.prepare_metadata_for_build_wheel(
            'metadata', config_settings)
        backend.prepare_metadata_for_build_editable(
            'metadata', config_settings)
        backend.build_editable('dist', config_settings)

        self.assertEqual(requirements, ['wheel', 'Cython'])
        self.assertEqual(build_values, ['1', '1', '1'])
        self.assertNotIn('PY3AMF_BUILD_CYTHON', os.environ)


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


class TutorialDocumentationTestCase(unittest.TestCase):
    unsupported_terms = (
        'appengine',
        'django',
        'elixir',
        'google app engine',
        'jython',
        'mod_python',
        'pylons',
        'sqlalchemy',
        'turbogears',
        'twisted',
        'web2py',
    )
    navigation_files = (
        'doc/tutorials/index.rst',
        'doc/tutorials/actionscript/index.rst',
        'doc/tutorials/apache/index.rst',
        'doc/html/tutorials.html',
    )

    def test_tutorial_navigation_excludes_unsupported_integrations(self):
        root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

        for filename in self.navigation_files:
            path = os.path.join(root, filename)

            if not os.path.exists(path):
                self.skipTest('source checkout documentation is not installed')

            with open(path, 'r') as fp:
                content = fp.read().lower()

            for term in self.unsupported_terms:
                self.assertNotIn(term, content, filename)


class MainTestCase(unittest.TestCase):
    def test_main_exits_non_zero_when_suite_fails(self):
        code = """
import unittest
import pyamf.tests

class FailingTestCase(unittest.TestCase):
    def test_failure(self):
        self.fail('expected failure')

pyamf.tests.get_suite = lambda: unittest.TestLoader().loadTestsFromTestCase(
    FailingTestCase
)
pyamf.tests.main()
"""
        result = subprocess.run(
            [sys.executable, '-c', textwrap.dedent(code)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        self.assertNotEqual(result.returncode, 0)
