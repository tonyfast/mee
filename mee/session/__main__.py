import nox
from pathlib import Path
import os, sys, importlib
from . import *

ROOT = Path().absolute()
if "LOAD_NOX_CONFIG" not in locals():
    LOAD_NOX_CONFIG = nox.tasks.load_nox_module

nox.options.noxfile = __file__


def load_nox_module(global_config):
    global ROOT
    try:
        return importlib.import_module(__name__)
    finally:
        os.chdir(ROOT)


nox.tasks.load_nox_module = load_nox_module

if __name__ == "__main__":
    from nox.__main__ import main

    sys.argv = sys.argv[:1] + sys.argv[1:]
    main()
