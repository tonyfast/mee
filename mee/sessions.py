import contextlib
from pathlib import Path

from nox import options, parametrize, session

options.sessions = ["config(mode='dev')"]


@contextlib.contextmanager
def prepare(session):
    cwd, name, *args = session.posargs
    session.cd(cwd)
    yield
    to = Path(name)
    if not to.exists():
        to.mkdir()

    session.cd(to)


def prepare_user(session, deps):
    with prepare(session):
        session.run(
            *f"pip install git+https://github.com/tonyfast/mee#egg=mee[{deps}]".split()
        )


def prepare_dev(session, deps):
    with prepare(session):
        session.install("flit")
        session.run(*f"flit install -s --deps production --extras {deps},dev".split())


@session(reuse_venv=True)
@parametrize("mode", ["dev", "user"])
def config(session, mode):
    cwd, name, *args = session.posargs

    (mode == "dev" and prepare_dev or prepare_user)(session, "config")
    session.run(*"python -m mee list".split())
    session.run(*f"python -m mee.tasks.dev dev -n {name}".split())
    session.run(*f"python -m mee.tasks.config submodules".split())

    session.run(*f"python -m mee.tasks.config jb mkdocs readme".split())


@session(reuse_venv=True)
def mkdocs(session):
    prepare(session, "mkdocs")
    session.run(*f"python -m mee.tasks.build mkdocs_build".split())


@session(reuse_venv=True)
def sphinx(session):
    prepare(session, "doc")
    session.run(*f"python -m mee.tasks.config readme conf_py".split())
    session.run(*f"python -m mee.tasks.build sphinx".split())
