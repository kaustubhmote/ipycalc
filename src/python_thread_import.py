#!/usr/bin/env python
# -*- coding: utf-8 -*-


def main():
    """
    Main thread

    This imports some of the basic elements that
    cannot be imported in a separate thread and
    starts the function import in a separate thread

    """
    import threading
    from rich import traceback
    from ipython_prompt import set_prompt

    # special case: rich tracebacks
    traceback.install()
    set_prompt("before")

    threading.Thread(target=do_import).start()


def do_import():
    """
    This functions does imports the required
    modules, functions and constants in a
    separated nonblocking thread.

    """
    import sys
    import os
    from matplotlib import use, style
    from ipython_prompt import set_prompt

    this = sys.modules[__name__]

    # special case: set matplotlib backend
    use("module://matplotlib-backend-kitty")
    style.use("dark_background")

    import_config("defaults/config.toml", this)
    for f in os.listdir("custom"):
        if f.startswith("config_"):
            import_config(f"custom/{f}", this)


    import_constants(this)
    import_custom_functions(this)


    # special case: pint unit registration
    from pint import UnitRegistry
    unit = UnitRegistry()
    setattr(this, 'unit', unit)

    set_prompt("after")


def import_config(config, global_scope):

    import tomllib
    with open(config, "rb") as f:
        cfg = tomllib.load(f)

    import_modules(cfg["modules"], global_scope)
    import_functions(cfg["functions"], global_scope)



def import_custom_functions(global_scope):
    """
    Imports functions from any file in this
    directory whose name starts with '_functions'.
    Only functions that have '[ipycalc entry point]'
    written somewhere in their docstrings are imported

    Parameters
    ----------
    global_scope : module
        the global module into which the functions should
        be imported

    """
    import os

    for dirc in ("defaults", "custom"):
        os.chdir(dirc)
        for f in os.listdir("."):
            if f.startswith("_functions"):

                functions = __import__(f.removesuffix(".py"))
                for function in dir(functions):
                    try:
                        f = getattr(functions, function)
                        if "[ipycalc entry point]" in f.__doc__:
                            setattr(global_scope, f.__name__, f)
                    except (AttributeError, TypeError):
                        pass
        os.chdir("..")


def import_modules(module_dict, global_scope):
    """
    Imports modules (and submodules) from the config
    file.

    Parameters
    ----------
    module_dict : dict
        dictionary containing the module names
    global_scope : module
        the global module into which the functions should
        be imported

    """
    import importlib

    imported_submodules = {}

    for alias, module in module_dict.items():
        imported_submodules[alias] = importlib.import_module(module)

    for alias, module in imported_submodules.items():
        setattr(global_scope, alias, module)


def import_functions(function_dict, global_scope):
    """
    Imports functions from the config file.

    Parameters
    ----------
    functions_dict : dict
        dictionary containing the function names and the 
        name of the module from which they should be 
        imported
    global_scope : module
        the global module into which the functions should
        be imported

    """
    import importlib

    imported_functions = {}
    for alias, module in function_dict.items():

        m = importlib.import_module(module)
        imported_functions[alias] = getattr(m, alias)

    for alias, function in imported_functions.items():
        setattr(global_scope, alias, function)


def import_constants(global_scope):
    """
    Imports all constants from a file called
    '_funcs_default.py'

    Parameters
    ----------
    global_scope : module
        the global module into which the functions should
        be imported

    """
    import os

    os.chdir("defaults")
    constants = __import__("_funcs_default") 

    for c in dir(constants):
        if not c.startswith("_"):
            setattr(global_scope, c, getattr(constants, c))

    os.chdir("..")

    os.chdir("custom")
    for f in os.listdir("."):
        if f.startswith("constants"):
            constants = __import__("custom/_constants") 

            for c in dir(constants):
                if not c.startswith("_"):
                    setattr(global_scope, c, getattr(constants, c))
    os.chdir("..")

if __name__ == "__main__":
    main()
