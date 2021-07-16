from nox import session
from pathlib import Path


@session(reuse_venv=True)
def user(session):
    name = session.posargs[0]
    to = Path(f"test-{name}")
    if not to.exists():
        to.mkdir()
    session.install("flit")
    session.run(*"flit install -s --deps production".split())
    session.cd(to)
    session.run(*"mee list".split())
    session.run(*f"mee dev -n {name}".split())
    session.run(*f"mee gist_api -n {name} -s 'one year ago'".split())
    session.run(*"mee gist_submodules".split())
    session.run(*"mee mkdocs readme toc config".split())


@session(reuse_venv=True)
def mkdocs(session):
    name = session.posargs[0]
    to = Path(f"test-{name}")

    session.cd(to)
    session.install(*"mkdocs mkdocs-jupyter".split())
    session.run(*"mkdocs build".split())


@session(reuse_venv=True)
def sphinx(session):
    name = session.posargs[0]
    to = Path(f"test-{name}")
    session.install("flit")
    session.run(*"flit install -s --deps production".split())
    session.cd(to)

    session.install(*"jupyter-book jupyterbook_latex".split())
    session.run(*"mee conf_py".split())
    session.run(*"sphinx-build . _build/html".split())
