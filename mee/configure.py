from doit import create_after
from pathlib import Path

# from .. import requires, get_NAME
# import os
from . import requires, main, DOIT_CONFIG, SETTINGS
import operator


class SINCE:
    params = [
        dict(name="name", short="n", default=SETTINGS.name, type=str),
        dict(name="since", short="s", default=SETTINGS.since, type=str),
    ]


def get_time(since, round="day"):
    import datetime

    import maya
    from maya import MayaDT

    time = maya.when(since)
    attrs = "year month day hour minute second microsecond".split()
    l = len(attrs)
    id = attrs.index(round) + 1
    args = operator.attrgetter(*attrs[:id])(time)
    args += tuple([0] * len(attrs[id:]))
    return MayaDT.from_datetime(
        datetime.datetime(*args, time.datetime().tzinfo)
    ).iso8601()


task_configure_r = requires(
    "requests", "requests_cache", "maya", "uritemplate", "sqlite_utils"
)


def get_gists(name=SETTINGS.name, since=SETTINGS.since):
    import uritemplate

    GITHUB = "https://api.github.com"
    GIST = uritemplate.URITemplate(GITHUB + "/users{/name}/gists{?page,since,per_page}")

    import requests
    import requests_cache

    requests_cache.install_cache(str(SETTINGS.db))
    url = GIST.expand(name=name, page=1, since=get_time(since), per_page=100)

    return requests.get(url)


def write_gists(name=SETTINGS.name, since=SETTINGS.since):
    """write gist content to a sqlite database

    we create three tables:
    * owner table
    * gist-content table containing files in gist
    * gist table containing top level gist info.
    """
    import sqlite_utils, sqlite3

    response = get_gists(name, since)

    db = sqlite_utils.Database(sqlite3.connect(SETTINGS.db))
    files = db["gist-content"]
    owner = db["github-owners"]
    gist = db["gist"]

    for i, row in enumerate(response.json()):
        owns = row.pop("owner")
        content = row.pop("files")
        files.insert_all(
            [
                {"path": row["id"] + "/" + x["filename"], "id": row["id"], **x}
                for x in content.values()
            ],
            pk="path",
            replace=True,
        )

        owner.insert(owns, pk="login", replace=True)
        gist.insert(
            {"owner": owns["id"], "files": list(content), **row},
            pk="html_url",
            replace=True,
        )
    print(f"loaded {i} gist")


def task_gist():
    """update data from the gist api"""
    return dict(
        actions=[write_gists],
        params=SINCE.params,
        setup=["configure_r"],
        targets=[SETTINGS.db],
    )


@create_after("gist")
def task_gist_submodule():
    """load gist as submodules from api data"""
    import sqlite_utils, sqlite3, json

    db = sqlite_utils.Database(sqlite3.connect(SETTINGS.db))
    table = db["gist"]
    for row in table.rows:
        if not row["public"]:
            continue
        if not row["description"]:
            continue
        dir = Path(SETTINGS.name)
        folder = dir / row["id"]
        yield dict(
            name=f"""submodule-add-{row["owner"]}-{row["id"]}""",
            file_dep=[".git/config"],
            actions=[f"""git submodule add --force {row["html_url"]} {folder}"""],
            targets=[folder / x for x in json.loads(row["files"])],
        )


from .compat.jb import *
from .compat.readme import *

create_after("gist_submodule")(task_jb)
create_after("gist_submodule")(task_readme)
if __name__ == "__main__":
    main(globals())
