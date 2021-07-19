import json
import collections
from mee.compat.jb import StdErr
from pathlib import Path

from pathspec.pathspec import PathSpec
from ..configure import task_configure_r
from .. import SETTINGS, main
from doit.task import clean_targets


def get_readme():
    import sqlite_utils, sqlite3, maya

    content = {}
    SETTINGS.config.initialize()

    db = sqlite_utils.Database(sqlite3.connect(SETTINGS.db))
    for name, info in SETTINGS.config.gitmodules.items():
        if name.startswith("submodule"):
            row = db["gist"].get(info["url"])
            content[maya.MayaDT.from_iso8601(row["created_at"])] = row

    days = collections.defaultdict(list)
    for when in sorted(content, reverse=True):
        row = content[when]
        if not row["description"]:
            continue
        days[format(when, "%D")].append(
            f"""### {row["description"]}\n\n"""
            + "\n".join(f"""* [{x}]({x})""" for x in json.loads(row["files"]))
        )
    from re import compile, IGNORECASE
    from fnmatch import translate

    try:
        profile = (
            next(
                x for x in Path().glob("*.md") if x.stem.lower() == "readme"
            ).read_text()
            + "\n\n---\n\n"
        )
    except StopIteration:
        profile = ""
    readme = profile + """# gists\n\n"""
    for key, value in days.items():
        readme += f"""## {key}\n\n\n""" + """\n\n---\n\n""".join(value) + "\n\n"

    return readme


def task_readme():
    """build a readme/index for the contents"""
    readme = Path(SETTINGS.name, "readme.md")

    def do():
        readme.write_text(get_readme())

    return dict(
        actions=[do],
        file_dep=[".gitmodules"],
        targets=[readme],
        setup=["configure_r"],
        clean=[clean_targets],
    )


if __name__ == "__main__":
    main(globals())
