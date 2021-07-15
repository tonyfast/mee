from functools import partial
from . import urls, utils
from pydantic import BaseModel, Field, AnyUrl
from enum import Enum
import enum
from pathlib import Path
from typing import List, Optional, ForwardRef, Union, Any

from pydantic.types import FilePath

import operator, datetime, collections, git


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
