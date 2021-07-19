from doit.task import clean_targets
from .. import requires, SETTINGS, main, DOIT_CONFIG
from pathlib import Path

task_sphinx_r = requires("jupyter-book")


def task_conf_py():
    """write the sphinx conf.py file"""
    return dict(
        actions=["jb config sphinx --toc toc.yml --config config.yml . > conf.py"],
        file_dep=["toc.yml", "config.yml"],
        targets=["conf.py"],
        clean=[clean_targets],
        setup=["sphinx_r"],
    )


def task_sphinx_build():
    """build the sphinx documentation"""
    return dict(
        actions=["sphinx-build . _build/html/ -vv", "touch _build/html/.nojekyll"],
        targets=["_build/html/index.html"],
        file_dep=["conf.py"],
    )


if __name__ == "__main__":
    main(globals())
