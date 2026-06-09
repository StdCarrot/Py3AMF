# Copyright (c) The PyAMF Project.
# See LICENSE.txt for details.

"""
Tools for doing dynamic imports.

@since: 0.3
"""
import importlib
import importlib.abc
import sys

__all__ = ['when_imported']


def when_imported(name, *hooks):
    """
    Call C{hook(module)} when module named C{name} is first imported. C{name}
    must be a fully qualified (i.e. absolute) module name.

    C{hook} must accept one argument: which will be the imported module object.

    If the module has already been imported, 'hook(module)' is called
    immediately, and the module object is returned from this function. If the
    module has not been imported, then the hook is called when the module is
    first imported.
    """
    global finder

    finder.when_imported(name, *hooks)


class ModuleLoader(importlib.abc.Loader):
    """
    Loader wrapper that delegates actual loading to the original loader and then
    runs post-import hooks.
    """

    def __init__(self, finder, name, loader):
        self.finder = finder
        self.name = name
        self.loader = loader

    def create_module(self, spec):
        if hasattr(self.loader, 'create_module'):
            return self.loader.create_module(spec)

        return None

    def exec_module(self, module):
        if hasattr(self.loader, 'exec_module'):
            self.loader.exec_module(module)
        else:
            # Compatibility fallback for old loaders.
            loaded = self.loader.load_module(self.name)

            if loaded is not module:
                module.__dict__.update(loaded.__dict__)

        self.finder._run_hooks(self.name, module)


class ModuleFinder(importlib.abc.MetaPathFinder):
    """
    This is a special module finder object that executes a collection of
    callables when a specific module has been imported. An instance of this
    is placed in C{sys.meta_path}, allowing us to provide this functionality.

    @ivar post_load_hooks: C{dict} of C{full module path -> callable} to be
        executed when the module is imported.
    @ivar loaded_modules: C{list} of modules that this finder has seen. Used
        to stop recursive imports.
    @see: L{when_imported}
    @since: 0.5
    """

    def __init__(self):
        self.post_load_hooks = {}
        self.loaded_modules = []

    def find_spec(self, name, path=None, target=None):
        """
        This is a new MoudleFinder implementation compatible with Py>=3.11

        Called when an import is made. If there are hooks waiting for this
        module to be imported then we wrap the normal loader and run hooks after
        the module has been executed.

        @param name: The name of the module being imported.
        @param path: The root path of the module, if importing from a package.
        @param target: Existing module object during reloads.
        @return: A ModuleSpec with a wrapped loader, or C{None} to allow the
            standard import process to continue.
        """
        if name in self.loaded_modules:
            return None

        hooks = self.post_load_hooks.get(name, None)

        if not hooks:
            return None

        self.loaded_modules.append(name)

        try:
            spec = self._find_wrapped_spec(name, path, target)
        except Exception:
            self.loaded_modules.pop()
            raise

        if spec is None or spec.loader is None:
            self.loaded_modules.pop()
            return None

        spec.loader = ModuleLoader(self, name, spec.loader)

        return spec

    def _find_wrapped_spec(self, name, path=None, target=None):
        """
        Find the real module spec without invoking this finder recursively.
        """
        meta_path = sys.meta_path[:]

        try:
            sys.meta_path.remove(self)
        except ValueError:
            pass

        try:
            return importlib.util.find_spec(name)
        finally:
            sys.meta_path[:] = meta_path

    def when_imported(self, name, *hooks):
        """
        @see: L{when_imported}
        """
        if name in sys.modules:
            for hook in hooks:
                hook(sys.modules[name])

            return

        h = self.post_load_hooks.setdefault(name, [])
        h.extend(hooks)

    def _run_hooks(self, name, module):
        """
        Run all hooks for a module.
        """
        try:
            hooks = self.post_load_hooks.pop(name, [])

            for hook in hooks:
                hook(module)
        finally:
            try:
                self.loaded_modules.remove(name)
            except ValueError:
                pass

    def __getstate__(self):
        return (self.post_load_hooks.copy(), self.loaded_modules[:])

    def __setstate__(self, state):
        self.post_load_hooks, self.loaded_modules = state



class LegacyModuleFinder(object):
    """
    This is original solution incompatible with Py>=3.11

    This is a special module finder object that executes a collection of
    callables when a specific module has been imported. An instance of this
    is placed in C{sys.meta_path}, which is consulted before C{sys.modules} -
    allowing us to provide this functionality.

    @ivar post_load_hooks: C{dict} of C{full module path -> callable} to be
        executed when the module is imported.
    @ivar loaded_modules: C{list} of modules that this finder has seen. Used
        to stop recursive imports in L{load_module}
    @see: L{when_imported}
    @since: 0.5
    """

    def __init__(self):
        self.post_load_hooks = {}
        self.loaded_modules = []

    def find_module(self, name, path=None):
        """
        Called when an import is made. If there are hooks waiting for this
        module to be imported then we stop the normal import process and
        manually load the module.

        @param name: The name of the module being imported.
        @param path The root path of the module (if a package). We ignore this.
        @return: If we want to hook this module, we return a C{loader}
            interface (which is this instance again). If not we return C{None}
            to allow the standard import process to continue.
        """
        if name in self.loaded_modules:
            return None

        hooks = self.post_load_hooks.get(name, None)

        if hooks:
            return self

    def load_module(self, name):
        """
        If we get this far, then there are hooks waiting to be called on
        import of this module. We manually load the module and then run the
        hooks.

        @param name: The name of the module to import.
        """
        self.loaded_modules.append(name)

        try:
            __import__(name, {}, {}, [])

            mod = sys.modules[name]
            self._run_hooks(name, mod)
        except:
            self.loaded_modules.pop()

            raise

        return mod

    def when_imported(self, name, *hooks):
        """
        @see: L{when_imported}
        """
        if name in sys.modules:
            for hook in hooks:
                hook(sys.modules[name])

            return

        h = self.post_load_hooks.setdefault(name, [])
        h.extend(hooks)

    def _run_hooks(self, name, module):
        """
        Run all hooks for a module.
        """
        hooks = self.post_load_hooks.pop(name, [])

        for hook in hooks:
            hook(module)

    def __getstate__(self):
        return (self.post_load_hooks.copy(), self.loaded_modules[:])

    def __setstate__(self, state):
        self.post_load_hooks, self.loaded_modules = state



def _init():
    """
    Internal function to install the module finder.
    """
    global finder

    if finder is None:
        if sys.version_info >= (3, 11):
            finder = ModuleFinder()
        else:
            finder = LegacyModuleFinder()

    if finder not in sys.meta_path:
        sys.meta_path.insert(0, finder)


finder = None
_init()
