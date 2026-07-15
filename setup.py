#!/usr/bin/env python

# Copyright (c) The PyAMF Project.
# See LICENSE.txt for details.

# import ordering is important
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import setupinfo
from setuptools import setup, find_packages


version = (0, 9, 1)

name = "Py3AMF"
description = "AMF support for Python"
long_description = setupinfo.read('README.rst')
url = "https://github.com/StdCarrot/Py3AMF"
author = "The Py3AMF Project"
author_email = "yhbu@stdc.so"
license = "MIT License"

classifiers = """
Intended Audience :: Developers
Intended Audience :: Information Technology
Natural Language :: English
Operating System :: OS Independent
Programming Language :: Python
Programming Language :: Python :: 3.11
Programming Language :: Python :: 3.12
Programming Language :: Python :: 3.13
Programming Language :: Python :: 3.14
Topic :: Internet :: WWW/HTTP :: WSGI :: Application
Topic :: Software Development :: Libraries :: Python Modules
"""

keywords = """
python3 amf amf0 amf3 flex flash remoting rpc http flashplayer air bytearray
objectproxy arraycollection recordset actionscript decoder encoder gateway wsgi
remoteobject sharedobject lso sol
"""


def setup_package():
    setupinfo.set_version(version)

    setupinfo.write_version_py()

    setup(
        name=name,
        version=setupinfo.get_version(),
        description=description,
        long_description=long_description,
        long_description_content_type="text/x-rst",
        url=url,
        author=author,
        author_email=author_email,
        keywords=' '.join(keywords.split()),
        license=license,
        packages=find_packages(),
        ext_modules=setupinfo.get_extensions(),
        install_requires=setupinfo.get_install_requirements(),
        zip_safe=False,
        extras_require=setupinfo.get_extras_require(),
        classifiers=(
            [_f for _f in classifiers.strip().split('\n') if _f] +
            setupinfo.get_trove_classifiers()
        ),
        **setupinfo.extra_setup_args())


if __name__ == '__main__':
    setup_package()
