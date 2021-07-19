"""a default gitignore configuration for mee

the gitignore is used to control the output of mee"""

from pathlib import Path
from .. import SETTINGS, main

DEFAULT = """!toc.yml
!config.yml
!mkdocs.yml
.env
"""


def task_gitignore():
    def do():
        Path(".gitignore").write_text(DEFAULT)
        SETTINGS.config.get_gitignore()

    return dict(actions=[do], targets=[".gitignore"])


if __name__ == "__main__":
    main(globals())
