import collections
import datetime
import enum
import json
import operator
from enum import Enum
from functools import partial
from pathlib import Path
from typing import Any, ForwardRef, List, Optional, Union

import git
from pydantic import AnyUrl, BaseModel, Field
from pydantic.types import FilePath

from . import urls, utils


def get_url(url):
    import requests
    import requests_cache

    requests_cache.install_cache(".mee")
    return requests.get(url)


class Markdown(str):
    def _repr_markdown_(self):
        return self


class BaseModel(BaseModel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if hasattr(self, "__post_init__"):
            self.__post_init__()


class PyProject(BaseModel):
    name: str


class Setup(BaseModel):
    class MetaData(BaseModel):
        name: str
        version: Optional[str]

        def __post_init__(self):
            import stringcase

            self.version = datetime.date.today().strftime("%Y.%M.%d.%H")

    class Options(BaseModel):
        install_requires: list = Field(default_factory=list)

    metadata: MetaData = Field(default_factory=MetaData)
    options: Options = Field(default_factory=Options)


class NonNull(BaseModel):
    def dict(self, *args, **kwargs):
        return {k: v for k, v in super().dict(*args, **kwargs).items() if v is not None}


class Collector(BaseModel):
    gitmodules: Optional[Any]
    gists: Optional[Any]
    ours: Optional[Any]
    df: Optional[Any]

    initialized: bool = False

    def init(self):
        if not self.initialized:
            self.get_gitmodules()
            self.get_our_gist_data()
            self.get_gists_data()
            self.get_tidy_data()
            self.initialized = True
        return self.df

    def get_gitmodules(self):
        import pandas

        self.gitmodules = pandas.DataFrame(
            utils.read(".gitmodules", ".cfg")._sections
        ).T.reset_index()
        print(self.gitmodules)
        self.gitmodules = (
            self.gitmodules.path.str.rpartition("/")[2]
            .rename("id")
            .pipe(self.gitmodules.join)
            .set_index("id")
        )
        return self.gitmodules

    def get_gists_data(self):
        import pandas

        self.gists = pandas.DataFrame(get_url(self.ours["url"]).json()).set_index("id")
        return self.gists

    def get_our_gist_data(self):
        self.ours = json.loads(Path("gists.json").read_text())
        return self.ours

    def get_tidy_data(self):
        import pandas

        df = self.gitmodules.join(self.gists.drop(columns="url"))

        for x in df.columns:
            if x.endswith("_at"):
                df[x] = df[x].pipe(pandas.to_datetime)

        df = (
            df.files.apply(lambda x: pandas.Series(list(x.values())))
            .stack()
            .apply(pandas.Series)
            .reset_index(-1, drop=True)
            .join(df)
        )

        df = pandas.concat({self.ours["name"]: df.set_index("filename", append=True)})

        df["dir"] = df.index.to_frame().apply("/".join, axis=1).apply(Path)
        df = df.sort_values("updated_at", ascending=False)
        df = df.set_index(df.updated_at.dt.round("D"), append=True)
        df = df.set_index(df.index.reorder_levels([-1, 0, 1, 2]))
        df = df.assign(
            nbviewer="https://nbviewer.jupyter.org/gist/"
            + df.drop(columns="updated_at")
            .reset_index()["level_1 id filename".split()]
            .apply("/".join, axis=1)
            .values,
            mybinder="https://mybinder.org/v2/gist/"
            + df.drop(columns="updated_at")
            .reset_index()["level_1 id".split()]
            .apply("/".join, axis=1)
            .values,
        )
        df.mybinder += "/HEAD?filepath=" + df.index.get_level_values("filename")

        assert df.description.astype(bool).all()
        self.df = df
        return df
