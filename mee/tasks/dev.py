import os
from pathlib import Path

from .. import utils
from . import DOIT_CONFIG, SINCE

DOIT_CONFIG["default_tasks"] = ["dev"]


def task_dev():
    """create a .env file for local development"""

    def create(name):
        assert name, f"a user name is required for local development"
        Path(".env").write_text(f"""GITHUB_ACTOR={name}""")

    return dict(
        actions=[create],
        uptodate=[os.getenv("CI") or False],
        task_dep=["git_init"],
        targets=[".env"],
        params=SINCE.params[:1],
    )


def task_git_init():
    return dict(actions=["git init"], uptodate=[Path(".git").exists()])


if __name__ == "__main__":
    from . import main

    main(globals())
