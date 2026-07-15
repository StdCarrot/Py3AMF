=====================
 Installation Guide
=====================

.. contents::

Py3AMF is a Python 3 package. CPython 3.11, 3.12, 3.13, and 3.14 are
tested. Older Python 3 versions are not intentionally blocked, but they
are outside the active test matrix.


Easy Installation
=================

Install the released package with pip_::

    python -m pip install Py3AMF

The runtime dependency set is intentionally small. To install the runtime
dependencies from a source checkout::

    python -m pip install -r requirements.txt


Manual Installation
===================

:doc:`community/download` and unpack the Py3AMF archive of your choice::

    tar zxfv Py3AMF-<version>.tar.gz
    cd Py3AMF-<version>

Install the package from the source directory::

    python -m pip install .


Optional Extras
===============

The only optional extra advertised by Py3AMF is lxml_ support for XML
handling::

    python -m pip install "Py3AMF[lxml]"

For source checkouts, the full test dependency set is listed in
``test-requirements.txt`` and includes lxml_.

Py3AMF no longer officially supports framework integration packages for
Django, Twisted, Google App Engine, SQLAlchemy, or Elixir.
Existing adapter and gateway modules remain in the source tree for
compatibility and application-level reuse, but framework-specific object
conversion should happen in application code before values are passed to
Py3AMF.

Cython extension builds are available as an explicit source-build option.
Default installs use the pure Python runtime. To compile the extensions, use
these lines in a requirements.txt file::

    --no-binary Py3AMF
    Py3AMF==0.9.1 --config-settings=py3amf.ext.cython=1

The ``Py3AMF[cython]`` extra is not used because extras select optional install
dependencies, not a new wheel build variant.
``--config-settings`` passes the build request directly to the backend.

Each part has a separate role:

``--no-binary Py3AMF``
    Tells pip not to select a prebuilt wheel for Py3AMF. Pip selects the source
    distribution instead and runs the local PEP 517 wheel build.

``--config-settings=py3amf.ext.cython=1``
    Passes the opt-in value to the Py3AMF build backend for this requirement.
    The backend adds Cython to the isolated build environment and enables the
    ``cpyamf`` extension modules.

Pip may reuse a compatible wheel that it built previously. Use
``python -m pip install --no-cache-dir -r requirements.txt`` when a clean source
rebuild is required.


Unit Tests
==========

Install the full test dependency set and run the default test suite::

    python -m pip install -r test-requirements.txt
    python -c "import pyamf.tests; pyamf.tests.main()"

The default suite covers the supported surface: AMF0, AMF3, core remoting,
WSGI gateway behavior, and dependency-free helpers. Legacy integration
suites for unsupported frameworks are not part of the default test entry
point.


Documentation
=============

Sphinx
------

To build the main documentation you need:

- Sphinx_ 1.0 or newer
- `sphinxcontrib.epydoc`_ 0.4 or newer
- a :doc:`copy <community/download>` of the Py3AMF source distribution

Unix users run the command below in the ``doc`` directory to create the
HTML version of the Py3AMF documentation::

    make html

Windows users can run the make.bat file instead::

    make.bat

This will generate the HTML documentation in the ``doc/build/html``
folder.

**Note**: if you don't have the `make` tool installed then you can invoke
Sphinx from the ``doc`` directory directly like this::

    sphinx-build -b html . build

Epydoc
------

To build the API documentation you need:

- Epydoc_ 3.0 or newer
- a :doc:`copy <community/download>` of the Py3AMF source distribution

Run the command below in the root directory to create the HTML version of
the PyAMF API documentation::

    epydoc --config=setup.cfg

This will generate the HTML documentation in the ``doc/build/api``
folder.


.. _Python: 			http://www.python.org
.. _pip:                       https://pip.pypa.io/
.. _Epydoc:			http://epydoc.sourceforge.net
.. _lxml:			http://lxml.de
.. _Sphinx:     		http://sphinx.pocoo.org
.. _sphinxcontrib.epydoc:       http://packages.python.org/sphinxcontrib-epydoc
