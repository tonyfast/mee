from .settings import Settings
from pathlib import Path

from .. import utils, requires
from . import DOIT_CONFIG, SINCE, CI

DOIT_CONFIG["default_tasks"] = ["dev"]
task_dotenv = requires(dotenv="python-dotenv")


def task_dev():
    """create a .env file for local development"""

    def create(name):
        assert name, f"a user name is required for local development"
        Path(".env").write_text(f"""GITHUB_ACTOR={name}""")

    return dict(
        actions=[create],
        uptodate=[CI or False],
        task_dep=["git_init"],
        setup=["dotenv"],
        targets=[".env"],
        params=SINCE.params[:1],
    )


def task_git_init():
    """initialize a git repo if there isn't one"""
    return dict(actions=["git init"], uptodate=[Path(".git").exists()])


if __name__ == "__main__":
    from . import main

    main(globals())
