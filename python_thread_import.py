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

    traceback.install()
    set_prompt("before")

    threading.Thread(target=do_import).start()


def do_import():
    """
    This functions does imports the required
    modules, functions and constants in a
    separated nonblocking thread.

    """
    import sys, toml
    from matplotlib import use, style
    from ipython_prompt import set_prompt

    this = sys.modules[__name__]

    use("module://matplotlib-backend-kitty")
    style.use("dark_background")

    cfg = toml.load("config.toml")

    import_modules(cfg["modules"], this)
    import_functions(cfg["functions"], this)
    import_constants(cfg["constants"], this)
    import_custom_functions(this)

    set_prompt("after")


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

    for f in os.listdir():
        if f.startswith("_functions"):

            functions = __import__(f.removesuffix(".py"))
            for function in dir(functions):
                try:
                    f = getattr(functions, function)
                    if "[ipycalc entry point]" in f.__doc__:
                        setattr(global_scope, f.__name__, f)
                except (AttributeError, TypeError):
                    pass


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


def import_constants(constant_dict, global_scope):
    """
    HERE BE DRAGONS! EVAL IS USED AND ALLOWS ARBITRARY CODE
    EXECUTION

    Imports constants from the config file.

    Parameters
    ----------
    constant_dict : dict
        dictionary containing the constant names and their
        execution functions
    global_scope : module
        the global module into which the functions should
        be imported

    """

    for alias, constant in constant_dict.items():
        setattr(global_scope, alias, eval(constant))


if __name__ == "__main__":
    main()
