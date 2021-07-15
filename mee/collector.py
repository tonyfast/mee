from . import urls, models, utils
from pathlib import Path
from .models import BaseModel, Config
from pydantic import FilePath
from typing import Optional, Any
import datetime, operator, collections, git
from functools import partial


class Collector(BaseModel):
    name: str = ""
    since: str = "one month ago"
    time: Optional[datetime.datetime]
    round: str = "day"
    path: FilePath = Path()
    repo: Optional[Any]
    gitmodules: Optional[Any]
    gitignore: Optional[Any]
    gists: Optional[Any]
    df: Optional[Any]
    submodules: Optional[list]

    order: Optional[list]

    def get_time(self):
        import maya
        from maya import MayaDT

        time = maya.when(self.since)
        attrs = "year month day hour minute second microsecond".split()
        l = len(attrs)
        id = attrs.index(self.round) + 1
        args = operator.attrgetter(*attrs[:id])(time)
        args += tuple([0] * len(attrs[id:]))
        self.time = MayaDT.from_datetime(
            datetime.datetime(*args, time.datetime().tzinfo)
        )

    def __post_init__(self):
        import git, os

        self.get_time()
        if os.getenv("CI") is None:
            import dotenv

            dotenv.load_dotenv()
        self.name = os.getenv("GITHUB_ACTOR")
        self.repo = git.Repo(self.path)

    def prior(self):
        import git

        self.repo = git.Repo(self.path)
        self.get_gist_data()

    def post(self):
        self.get_submodules()
        self.get_gitignore()
        self.get_tidy_df()
        return self

    def expand(self):
        import git

        self.repo = git.Repo(self.path)

        self.get_gitignore()
        self.get_submodules()
        self.get_tidy_df()
        return self

    def get_tidy_df(self):
        import pandas

        self.df = self.gists.loc[[x["url"] for x in self.submodules]]
        self.df = (
            self.df.files.apply(lambda x: pandas.Series(list(x.values())))
            .stack()
            .apply(pandas.Series)
            .reset_index(-1, drop=True)
            .join(self.df)
            .drop(columns="files")
            .join(pandas.DataFrame(self.submodules).set_index("url").applymap(Path))
            .set_index("filename", append=True)
        )
        self.get_submodule_data()
        self.df["last_commit_at"] = self.df.history.apply(max)
        self.df["first_commit_at"] = self.df.history.apply(min)
        self.df["changes"] = self.df.history.apply(len)
        self.get_right_times()
        self.order = list(
            self.df.updated_at.sort_values(ascending=False)
            .index.get_level_values(0)
            .drop_duplicates()
        )

    def get_right_times(self):
        import pandas

        for column in self.df.columns:
            if column.endswith("_at"):
                self.df[column] = self.df[column].pipe(pandas.to_datetime, utc=True)

    def get_submodules(self):
        self.gitmodules = utils.read(self.path / ".gitmodules", ".cfg")
        self.submodules = []
        for section in self.gitmodules.sections():
            if section.startswith("submodule"):
                self.submodules.append(dict(self.gitmodules[section]))

    def get_gitignore(self):
        from pathspec import PathSpec

        try:
            self.gitignore = PathSpec.from_lines(
                (self.path / ".gitignore").read_text().splitlines()
            )
        except FileNotFoundError:
            self.gitignore = PathSpec([])

    def get_gist_data(self):
        import requests_cache, pandas, requests

        requests_cache.install_cache(".mee")
        self.gists = pandas.DataFrame(
            requests.get(
                urls.GIST.expand(
                    name=self.name, page=1, since=self.time.iso8601(), per_page=100
                )
            ).json()
        )
        self.gists = self.gists.set_index("html_url")

    def get_submodule_data(self):
        for i in self.df.index.drop_duplicates():
            df = self.df.loc[[i]]
            authors = set()
            history = collections.defaultdict(dict)
            for commit in git.Repo(df.path.iloc[0]).iter_commits():
                authors.add(commit.author.name)
                for blob in commit.tree.blobs:
                    if blob.name in df.index.get_level_values("filename"):
                        history[blob.name][commit.committed_datetime] = blob.size

            self.df.loc[[i], "history"] = list(
                self.df.loc[[i]].index.get_level_values("filename").map(history.get)
            )
            self.df.loc[[i], "authors"] = [authors] * len(self.df.loc[[i]])

        for submodule in self.submodules:
            self.df.loc[submodule["url"]] = (
                self.df.loc[submodule["url"]].assign(**submodule).values
            )

        self.df.path = self.df.path.apply(Path)

        self.df.path = self.df.apply(lambda s: s.path / s.name[1], axis=1)

    def get_readme(self):
        import pandas, stringcase, jinja2

        df = self.df[
            self.df.path.apply(
                lambda x: x.suffix in ".ipynb .md .markdown .rst".split()
            )
        ]
        readme = collections.defaultdict(partial(collections.defaultdict, list))
        for i, s in df.groupby(
            [
                pandas.Grouper(freq="M", key="updated_at"),
                pandas.Grouper(freq="D", key="updated_at"),
                df.index.get_level_values(0),
            ]
        ):
            readme[i[0]][i[1]].append(df.loc[[i[2]]])
        HR = """---
"""
        body = """"""

        for month, items in reversed(readme.items()):
            body += month.to_pydatetime().strftime("\n## %B\n\n")
            for day, frames in items.items():

                body += day.to_pydatetime().strftime("\n### %D\n\n")
                for g in reversed(frames):
                    body += g.pipe(
                        lambda df: jinja2.Template(
                            """> {{df.description.iloc[0]}}

{% for id, file in df.index -%}
* [{{file}}]({{df.index.get_level_values(0)[0]}}#file-{{stringcase.spinalcase(file)}})
{% endfor %}
"""
                        ).render(df=df, stringcase=stringcase)
                    )

                body += "\n\n---\n"
        return models.Markdown(body)

    def get_toc(self):
        import pandas

        toc = dict(parts=[])
        for i, s in reversed(
            list(
                self.df.groupby(
                    [
                        pandas.Grouper(freq="M", key="updated_at"),
                        pandas.Grouper(freq="D", key="updated_at"),
                        self.df.index.get_level_values(0),
                    ]
                )
            )
        ):
            toc["parts"].append(
                dict(
                    chapters=list(
                        s.path.apply(lambda x: dict(file=str(x.with_suffix(""))))
                    ),
                    caption=s.description.iloc[0],
                )
            )
        return toc

    def get_jb_config(self):
        return models.Config(title=self.config.name, author=self.config.name)
