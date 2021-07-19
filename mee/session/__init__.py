from pathlib import Path

from nox import options, parametrize, session
from .. import SETTINGS


options.sessions = []


def prepare(session, mode):
    if mode == "dev":
        ROOT = Path().absolute()
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
@parametrize("mode", ["dev", "user", "main"])
def sphinx(session, mode):
    prepare(session, mode)
    session.run(*"python -m mee.compat.sphinx".split(), *session.posargs)
