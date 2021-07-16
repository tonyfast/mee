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


def get_toc(df):
    owner = df["owner"][0]
    toc = dict(parts=[], root=owner["login"] + "/readme")
    df = df[df.dir.apply(str).str.endswith(tuple(".ipynb .md .markdown".split()))]

    for day in df.index.get_level_values("updated_at").drop_duplicates():
        for path in df.loc[day].index.get_level_values(0).drop_duplicates():
            for id in df.loc[day].loc[path].index.get_level_values(0).drop_duplicates():
                g = df.loc[day].loc[path].loc[id]
                toc["parts"].append(
                    dict(
                        caption=day.to_pydatetime().strftime("%D")
                        + " "
                        + g.description[0].lstrip(),
                        chapters=[
                            dict(file=str(x.dir.with_suffix("")))
                            for i, x in g.iterrows()
                        ],
                    )
                )
    return Toc(**toc)


def get_config(df):
    owner = df["owner"][0]
    return Config(name=owner["login"], title=owner["login"], logo=owner["avatar_url"])
