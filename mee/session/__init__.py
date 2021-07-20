from pathlib import Path

from nox import options, parametrize, session
from .. import SETTINGS

ROOT = Path().absolute()
HERE = Path(__file__).parent.absolute()
options.sessions = []


def prepare(session, mode):
    if mode == "dev":

        session.install("flit")
        session.cd("/home/tonyfast/Documents/moi")
        session.run(*"flit install -s --deps production".split())
        session.cd(str(ROOT))
    elif mode == "user":
        session.install("mee")
    else:
        session.install("git+https://github.com/tonyfast/mee")


@session(reuse_venv=True)
@parametrize("mode", ["dev", "user", "main"])
def configure(session, mode):
    prepare(session, mode)
    session.run(*"python -m mee.configure".split(), *session.posargs)


@session(reuse_venv=True)
def sphinx(session):
    session.install("jupyter-book", "doit")
    dodo = HERE.parent / "compat" / "sphinx.py"
    session.run(
        *"python -m doit".split(),
        "-f",
        str(dodo),
        "-d",
        str(ROOT),
        *session.posargs,
        success_codes=[0, 2]
    )


@session(reuse_venv=True)
def nikola(session):
    session.install("nikola", "ruamel.yaml", "notebook")

    session.run(*"python -m nikola".split(), *session.posargs or ["build"])
