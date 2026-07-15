======================
  Future Development
======================

Current project planning is maintained in ``ROADMAP.md`` at the repository
root.

The project focuses on a small supported surface:

- CPython 3.11 through 3.14 in the test matrix.
- AMF0 and AMF3 codecs.
- Core remoting behavior.
- The WSGI gateway.
- Pure Python runtime code.
- Optional Cython extension builds.
- ``pyamf.adapters`` helper modules for compatibility and application-level
  reuse.

Jython, legacy framework gateways, and automatic conversion of third-party
framework models are no longer official goals for the supported runtime
surface.
