# our configuration is based on environment variables.
# this is because the primary target is to work on ci.
# we'll use https://docs.github.com/en/actions/reference/environment-variables
# as the references naming

import os, appdirs
from pathlib import Path
from functools import partial
from pydantic import DirectoryPath

from .models import BaseModel, FilePath, Optional, Any, Field, AnyUrl, List

CI = os.getenv("CI")

if not CI and Path(".env").exists():
    import dotenv

    dotenv.load_dotenv()


class Settings(BaseModel):
    dir: DirectoryPath = Path().absolute()
    binder: AnyUrl = os.getenv("BINDER_URL")
    ci: bool = bool(CI)
    name: str = os.getenv("GITHUB_ACTOR")
    branch: str = os.getenv("GITHUB_REF")
    since: str = "six months ago"
    data_dir: DirectoryPath = Path(appdirs.user_data_dir("Mee", "Deathbeds"))
    db: FilePath = data_dir / "mee.sqlite"
    DOIT_CONFIG: dict = Field(default_factory=partial(dict, verbosity=2))

    class EntryPoints(BaseModel):
        names = "configure build".split()
        initialized: bool = False
        configure: list = Field(default_factory=list)
        build: list = Field(default_factory=list)

        def initialize(self):
            if not self.initialized:
                from importlib.metadata import entry_points

                entry_points = entry_points()
                for key in self.names:
                    setattr(self, key, entry_points[f"mee.{key}"])
                self.initialized = True

    entry_points: EntryPoints = Field(default_factory=EntryPoints)

    class Conventions(BaseModel):
        initialized: bool = False

        gitignore: Optional[Any]
        gitmodules: Optional[dict]
        gitinclude: Optional[List[FilePath]]

        def initialize(self):
            if not self.initialized:
                self.get_gitignore()
                self.get_gitmodules()
            self.initialized = True

        def get_gitmodules(self):
            import configparser

            gitmodules = Path(".gitmodules")
            parser = configparser.ConfigParser()
            if gitmodules.exists():
                parser.read_string(gitmodules.read_text())
            self.gitmodules = parser._sections

        def get_gitignore(self):
            from pathspec import PathSpec
            from pathspec.patterns import GitWildMatchPattern

            self.gitinclude = []

            gitignore = Path(".gitignore")
            self.gitignore = PathSpec.from_lines(
                GitWildMatchPattern,
                [
                    line.startswith("!") and self.gitinclude.append(Path(line[1:]))
                    for line in gitignore.read_text().splitlines()
                ]
                if gitignore.exists()
                else [],
            )

    config: Conventions = Field(default_factory=Conventions)

    def __post_init__(self):
        self.data_dir.mkdir(exist_ok=True, parents=True)

        if not self.branch:
            from doit.tools import CmdAction

            action = CmdAction("git branch --show-current".split(), shell=False)
            action.execute()
            self.branch = action.result.strip()


if __name__ == "__main__":
    import pprint

    settings = Settings()
    settings.config.get_gitignore()
    pprint.pprint(settings.dict())
