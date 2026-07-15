# Copyright (c) The PyAMF Project.
# See LICENSE.txt for details.

"""PEP 517 build backend for optional Py3AMF extensions."""

from contextlib import contextmanager
import os

from setuptools import build_meta as _build_meta


def _is_truthy(value):
    if isinstance(value, (list, tuple)):
        return any(_is_truthy(item) for item in value)

    if isinstance(value, str):
        return value.strip().lower() in {
            '1', 'y', 'yes', 't', 'true', 'on'
        }

    return bool(value)


def cython_enabled(config_settings):
    if not config_settings:
        return False

    return _is_truthy(config_settings.get('py3amf.ext.cython'))


@contextmanager
def _build_environment(config_settings):
    name = 'PY3AMF_BUILD_CYTHON'
    previous = os.environ.pop(name, None)

    if cython_enabled(config_settings):
        os.environ[name] = '1'

    try:
        yield
    finally:
        os.environ.pop(name, None)

        if previous is not None:
            os.environ[name] = previous


def get_requires_for_build_wheel(config_settings=None):
    return _get_requires_for_binary_build(
        _build_meta.get_requires_for_build_wheel, config_settings)


def _get_requires_for_binary_build(hook, config_settings):
    requirements = list(hook(config_settings))

    if cython_enabled(config_settings) and 'Cython' not in requirements:
        requirements.append('Cython')

    return requirements


def prepare_metadata_for_build_wheel(metadata_directory,
                                     config_settings=None):
    with _build_environment(config_settings):
        return _build_meta.prepare_metadata_for_build_wheel(
            metadata_directory, config_settings)


def build_wheel(wheel_directory, config_settings=None,
                metadata_directory=None):
    with _build_environment(config_settings):
        return _build_meta.build_wheel(
            wheel_directory, config_settings, metadata_directory)


def build_sdist(sdist_directory, config_settings=None):
    return _build_meta.build_sdist(sdist_directory, config_settings)


def get_requires_for_build_sdist(config_settings=None):
    return _build_meta.get_requires_for_build_sdist(config_settings)


def get_requires_for_build_editable(config_settings=None):
    return _get_requires_for_binary_build(
        _build_meta.get_requires_for_build_editable, config_settings)


def prepare_metadata_for_build_editable(metadata_directory,
                                        config_settings=None):
    with _build_environment(config_settings):
        return _build_meta.prepare_metadata_for_build_editable(
            metadata_directory, config_settings)


def build_editable(wheel_directory, config_settings=None,
                   metadata_directory=None):
    with _build_environment(config_settings):
        return _build_meta.build_editable(
            wheel_directory, config_settings, metadata_directory)
