from functools import partial
from . import urls, utils
from pydantic import BaseModel, Field, AnyUrl
from enum import Enum
import enum, json
from pathlib import Path
from typing import List, Optional, ForwardRef, Union, Any

from pydantic.types import FilePath

import operator, datetime, collections, git


def get_url(url):
    import requests_cache, requests

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


class FORMAT(Enum):
    jb_book = "jb-book"
    jb_article = "jb-article"


class Entry(NonNull):
    file: Optional[Union[str, FilePath]]
    glob: Optional[str]
    url: Optional[AnyUrl]
    title: Optional[str]
    sections: Optional[ForwardRef("Entry")]


Entry.update_forward_refs()


class Chapter(NonNull):
    caption: Optional[str]
    chapters: Optional[List[Entry]]


class Content(NonNull):
    chapters: Optional[List[Entry]]
    parts: Optional[List[Chapter]]
    sections: Optional[List[Entry]]


class Toc(Content):
    format: FORMAT = "jb-book"
    root: str = "readme"

    def append(self, section):
        self.sections = self.sections or []
        self.sections.append(section)
        return self


class EXECUTE(Enum):
    auto = "auto"
    force = "force"
    cache = "cache"
    off = "off"


class StdErr(Enum):
    show = "show"
    remove = "remove"
    remove_warn = "remove-warn"
    warn = "warn"
    error = "error"
    severe = "severe"


class TEX(Enum):
    pdflatex = "pdflatex"
    xelatex = "xelatex"
    luatex = "luatex"
    platex = "platex"
    uplatex = "uplatex"


class Comments(BaseModel):
    hypothesis: bool = False
    utterances: bool = False


class Config(NonNull):
    class Execute(BaseModel):
        execute_notebooks: EXECUTE = "off"
        cache: str = ""
        exclude_patterns: List[str] = Field(default_factory=list)
        timeout: float = 30
        run_in_temp: bool = True
        allow_errors: bool = True

    class Parse(BaseModel):
        myst_enable_extensions: List[str] = Field(
            default_factory=lambda: "linkify substitution dollarmath colon_fence".split()
        )
        myst_url_schemes: List[str] = Field(
            default_factory=lambda: "mailto http https".split()
        )

    class Html(BaseModel):
        favicon: str = ""
        use_edit_page_button: bool = False
        use_repository_button: Union[bool, str] = False
        use_issues_button: bool = False
        use_multitoc_numbering: bool = True
        extra_navbar: str = ""
        extra_footer: str = ""
        google_analytics_id: str = ""
        home_page_in_navbar: bool = True
        baseurl: str = ""
        comments: Optional[Comments] = Field(default_factory=Comments)

    class Latex(BaseModel):
        latex_engine: TEX = "pdflatex"
        use_jupyterbook_latex: bool = True

    class Buttons(BaseModel):
        pass

    class Sphinx(BaseModel):
        pass

    class Repository(BaseModel):
        pass

    title: Optional[str]
    author: Optional[str]
    copyright: Optional[str]
    logo: Optional[str]
    exclude_patterns: List = Field(default_factory=list)
    only_build_toc_files: bool = True
    stderr_output: Optional[StdErr]

    execute: Optional[Execute] = Field(default_factory=Execute)
    parse: Optional[Parse] = Field(default_factory=Parse)
    html: Optional[Html] = Field(default_factory=Html)
    repository: Optional[Repository] = Field(default_factory=Repository)
    launch_buttons: Optional[Buttons] = Field(default_factory=Buttons)
    latex: Optional[Latex] = Field(default_factory=Latex)


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
