from doit.task import clean_targets
from ..settings import Settings
from functools import partial
from .. import tools, main, DOIT_CONFIG, SETTINGS
import json
from pathlib import Path
from ..models import (
    Any,
    AnyUrl,
    BaseModel,
    Enum,
    Field,
    FilePath,
    ForwardRef,
    List,
    NonNull,
    Optional,
    Union,
)


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
        use_jupyterbook_latex: bool = False

    class Buttons(BaseModel):
        pass

    class Sphinx(NonNull):
        class Nikola(NonNull):
            BLOG_AUTHOR: str
            BLOG_TITLE: str
            SITE_URL: Optional[AnyUrl]
            BLOG_EMAIL: Optional[str]
            BLOG_DESCRIPTION: str
            DEFAULT_LANG: str = "en"
            POSTS: list = Field(
                default_factory=partial(
                    list,
                    (
                        # ("tonyfast/*.rst", "posts", "post.tmpl"),
                        ("tonyfast/*.md", "posts", "post.tmpl"),
                        ("tonyfast/*.ipynb", "posts", "post.tmpl"),
                        # ("tonyfast/*.html", "posts", "post.tmpl"),
                    ),
                )
            )
            PAGES: list = Field(default_factory=list)

        extra_extensions: Optional[list]
        local_extensions: Optional[list]
        config: Nikola = Field(default_factory=Nikola)

    class Repository(BaseModel):
        pass

    title: Optional[str]
    author: Optional[str]
    copyright: Optional[str]
    logo: Optional[str]
    exclude_patterns: List = Field(default_factory=partial(list, [".nox", "_build"]))
    only_build_toc_files: bool = False
    stderr_output: Optional[StdErr]

    execute: Optional[Execute] = Field(default_factory=Execute)
    parse: Optional[Parse] = Field(default_factory=Parse)
    html: Optional[Html] = Field(default_factory=Html)
    repository: Optional[Repository] = Field(default_factory=Repository)
    launch_buttons: Optional[Buttons] = Field(default_factory=Buttons)
    latex: Optional[Latex] = Field(default_factory=Latex)
    sphinx: Sphinx = Field(default_factory=Sphinx)


def get_toc():
    import sqlite_utils, sqlite3, maya

    content = {}
    SETTINGS.config.initialize()
    db = sqlite_utils.Database(sqlite3.connect(SETTINGS.db))
    for name, info in SETTINGS.config.gitmodules.items():
        if name.startswith("submodule"):
            row = db["gist"].get(info["url"])
            content[maya.MayaDT.from_iso8601(row["created_at"])] = row

    parts = []
    for when in sorted(content, reverse=True):
        row = content[when]
        if not row["description"]:
            continue
        parts.append(
            dict(
                caption=f"""{when:%D} {row["description"]}""",
                chapters=[
                    dict(file=str(Path(SETTINGS.name, row["id"], x).with_suffix("")))
                    for x in json.loads(row["files"])
                ],
            )
        )

    return Toc(root=f"""{SETTINGS.name}/readme""", parts=parts)


def get_config():
    return Config(
        name=SETTINGS.name,
        title=SETTINGS.name,
        sphinx=Config.Sphinx(
            config=Config.Sphinx.Nikola(
                BLOG_AUTHOR=SETTINGS.name,
                BLOG_TITLE=SETTINGS.name,
                BLOG_DESCRIPTION=SETTINGS.name,
            )
        ),
    )


task_yaml_r = tools.requires(ruamel="ruamel.yaml")


def task_jb():
    """write the jupyter book configuration files"""

    def export_toc():
        tools.write("toc.yml", get_toc().dict())

    def export_config():
        tools.write("config.yml", get_config().dict())

    return dict(
        file_dep=[".gitmodules"],
        actions=[export_toc, export_config],
        targets=["toc.yml", "config.yml"],
        clean=[clean_targets],
        setup=["yaml_r"],
    )


if __name__ == "__main__":
    main(globals())
