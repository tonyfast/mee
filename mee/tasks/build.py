from .. import utils


def task_mkdocs():
    """build docs with mkdocs"""
    return dict(
        file_dep=["mkdocs.yml"],
        actions=["mkdocs build"],
        targets=["_build/html/mkdocs/readme.html"],
    )


def task_sphinx():
    """build the sphinx documentation"""
    return dict(
        actions=["sphinx-build . _build/html/"],
        targets=["_build/html/index.html"],
        file_dep=["conf.py"],
    )


if __name__ == "__main__":
    from . import main

    main(globals())
