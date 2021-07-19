import json
import collections
from pathlib import Path
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
            + "\n".join(map("* ".__add__, json.loads(row["files"])))
        )

    readme = """# gists\n\n"""
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
