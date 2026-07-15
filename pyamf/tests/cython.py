# Copyright (c) The PyAMF Project.
# See LICENSE.txt for details.

"""Run the supported test suite against the Cython codec implementations."""

import importlib
import importlib.machinery
import sys
import types
import unittest

import pyamf
import pyamf.tests


CODEC_MODULES = ('amf0', 'amf3')
EXTENSION_MODULES = ('amf0', 'amf3', 'codec', 'util')


class _CodecFacade(types.ModuleType):
    def __init__(self, pure_module, extension_module):
        super(_CodecFacade, self).__init__(pure_module.__name__)
        super(_CodecFacade, self).__setattr__(
            '_pure_module', pure_module)
        super(_CodecFacade, self).__setattr__(
            '_extension_module', extension_module)

    def __getattr__(self, name):
        if name in ('Encoder', 'Decoder'):
            return getattr(self._extension_module, name)

        return getattr(self._pure_module, name)

    def __setattr__(self, name, value):
        if name.startswith('_'):
            super(_CodecFacade, self).__setattr__(name, value)
        else:
            setattr(self._pure_module, name, value)

    def __dir__(self):
        return sorted(set(
            dir(self._pure_module) + dir(self._extension_module)))


def inject_extension_codecs(test_modules):
    """Inject Cython codec classes into the AMF modules used by tests."""
    extension_modules = {}

    for name in CODEC_MODULES:
        pure_module = importlib.import_module('pyamf.' + name)
        extension_module = importlib.import_module('cpyamf.' + name)
        facade = _CodecFacade(pure_module, extension_module)

        extension_modules[name] = extension_module

        for test_module in test_modules:
            for attribute, value in vars(test_module).copy().items():
                if value is pure_module:
                    setattr(test_module, attribute, facade)

    return extension_modules


class CythonModulesTestCase(unittest.TestCase):
    def test_cython_modules_are_binary_extensions(self):
        suffixes = tuple(importlib.machinery.EXTENSION_SUFFIXES)

        for name in EXTENSION_MODULES:
            module = importlib.import_module('cpyamf.' + name)

            self.assertTrue(
                module.__file__.endswith(suffixes), module.__file__)

    def test_explicit_cython_codecs_round_trip(self):
        payload = {
            'items': [1, True, None],
            'message': 'hello',
        }

        for encoding in (pyamf.AMF0, pyamf.AMF3):
            encoder = pyamf.get_encoder(encoding, use_ext=True)
            self.assertTrue(
                encoder.__class__.__module__.startswith('cpyamf.'))

            encoder.writeElement(payload)
            stream = encoder.stream
            stream.seek(0)

            decoder = pyamf.get_decoder(
                encoding, stream.getvalue(), use_ext=True)
            self.assertTrue(
                decoder.__class__.__module__.startswith('cpyamf.'))
            self.assertEqual(decoder.readElement(), payload)


def get_suite():
    suite = pyamf.tests.get_suite()
    test_modules = {
        sys.modules[test.__class__.__module__]
        for test in _iter_tests(suite)
    }

    inject_extension_codecs(test_modules)
    suite.addTest(
        unittest.TestLoader().loadTestsFromTestCase(CythonModulesTestCase))

    return suite


def _iter_tests(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            for test in _iter_tests(item):
                yield test
        else:
            yield item


def main():
    result = unittest.TextTestRunner().run(get_suite())

    sys.exit(not result.wasSuccessful())


if __name__ == '__main__':
    main()
