from os import path
from . import urls, utils
import requests_cache, requests, maya, functools, pathlib, git


class PARAMS:
    NAME = [dict(name="name", type=str, default="tonyfast")]
    GIST = NAME + [
        dict(name="page", type=int, default=1),
        dict(name="since", type=str, default="one month ago"),
    ]


def blank(callable):
    @functools.wraps(callable)
    def main(*args, **kwargs):
        callable(*args, **kwargs)

    return main


def get_gist(name, page=1, since="one month ago"):
    requests_cache.install_cache("xxx")
    since = maya.when(since)
    date, sep, time = since.iso8601().partition("T")
    since = date + sep + "00:00:00.000000Z"
    return requests.get(
        urls.GIST.expand(name=name, page=page, per_page=100, since=since)
    )


def task_clear():
    """clear the requests cache"""

    def clear():
        requests_cache.install_cache("xxx")
        requests_cache.clear()

    return dict(actions=[clear])


def task_initialize_gist():
    """initialize the user gist data"""
    return dict(
        actions=[blank(get_gist)],
        params=PARAMS.GIST,
    )


def get_submodules(name, page=1, since="one month ago"):
    import pandas

    df = pandas.DataFrame(get_gist(name, page, since).json()).set_index("id")
    NAME = pathlib.Path(name)
    NAME.mkdir(exist_ok=True)
    repo = git.Repo()
    for i in df[df.description.astype(bool)].index:
        target = NAME / i
        if not target.exists():
            try:
                repo.git.execute(
                    f"""git submodule add {df.loc[i]["git_pull_url"]} {target}""".split()
                )
            except git.GitCommandError:
                repo.git.execute(
                    f"""git submodule add --force {df.loc[i]["git_pull_url"]} {target}""".split()
                )


def task_submodules():
    return dict(
        actions=[get_submodules, "git submodule init", "git submodule update"],
        task_dep=["initialize_gist"],
        params=PARAMS.GIST,
    )
