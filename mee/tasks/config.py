import json
import os
from pathlib import Path

import doit
from doit.loader import create_after
from doit.task import clean_targets

from .. import urls, utils
from . import COLLECTOR, NAME, get_time
from .dev import *


def get(name=NAME, since="three months ago"):
    import requests
    import requests_cache

    requests_cache.install_cache(".mee")
    url = urls.GIST.expand(name=name, page=1, since=get_time(since), per_page=100)

    Path("gists.json").write_text(
        json.dumps(
            dict(
                url=url,
                name=name,
                since=since,
                gists=[
                    dict(
                        id=x["id"],
                        description=x["description"],
                        url=x["html_url"],
                        files=list(x["files"]),
                    )
                    for x in requests.get(url).json()
                ],
            )
        )
    )


def task_submodule():
    return dict(
        actions=["git submodule add %{url} %{name}"],
        params=[dict(name="url", short="u", long="url", type=str)] + SINCE.params[:1],
    )


def task_gist_api():
    return dict(actions=[get], params=SINCE.params, targets=[NAME + "/gists.json"])


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


@create_after("gist_api")
def task_submodules():
    try:
        with open("gists.json") as file:
            data = json.load(file)
    except FileNotFoundError:
        return dict(actions=["echo 'uninitialized'"])
    yield dict(
        name="create_target", actions=[(doit.tools.create_folder, [data["name"]])]
    )
    targets = []
    for gist in data["gists"]:
        if gist["description"]:
            target = [f"""{data["name"]}/{gist["id"]}/{x}""" for x in gist["files"]]
            yield dict(
                name=f"""submodule-{gist["id"]}""",
                actions=[
                    f"""git submodule add --force {gist["url"]} {data["name"]}/{gist["id"]}"""
                ],
                file_dep=["gists.json"],
                targets=target,
            )
            targets += target
    yield dict(
        name="update-submodules", file_dep=targets, actions=["git submodule update"]
    )


def task_git_init():
    return dict(actions=["git init"], uptodate=[Path(".git").exists()])


def task_jb():
    """write the jupyter book configuration files"""
    from ..compat import jb

    def export_toc():
        utils.write("toc.yml", jb.get_toc(COLLECTOR.init()).dict())

    def export_config():
        utils.write("config.yml", jb.get_config(COLLECTOR.init()).dict())

    return dict(
        file_dep=[".gitmodules"],
        actions=[export_toc, export_config],
        targets=["toc.yml", "config.yml"],
        clean=[clean_targets],
    )


def task_mkdocs():
    """configure mkdocs"""
    from ..compat import mkdocs

    def export_mkdocs():
        utils.write("mkdocs.yml", mkdocs.get_mkdocs(COLLECTOR.init()).dict())

    return dict(
        file_dep=[".gitmodules"],
        actions=[export_mkdocs],
        targets=["mkdocs.yml"],
        clean=[clean_targets],
    )


def task_mkdocs_build():
    """build docs with mkdocs"""
    return dict(
        file_dep=["mkdocs.yml"],
        actions=["mkdocs build"],
        targets=["_build/html/mkdocs/readme.html"],
    )


def task_readme():
    def export_readme():
        from ..compat import readme

        Path(NAME, "readme.md").write_text(readme.get_readme(COLLECTOR.init()))

    return dict(
        actions=[export_readme],
        targets=[NAME + "/readme.md"],
        file_dep=[".gitmodules", "gists.json"],
        clean=[clean_targets],
    )


def task_conf_py():
    """write the sphinx conf.py file"""
    return dict(
        actions=["jb config sphinx --toc toc.yml --config config.yml . > conf.py"],
        file_dep=[Path(NAME, "readme.md"), "toc.yml", "config.yml"],
        targets=["conf.py"],
    )


if __name__ == "__main__":
    from . import main

    main(globals())
