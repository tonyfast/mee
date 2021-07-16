from ..models import BaseModel, Field
from typing import List, Optional


def get_mkdocs(df):
    owner = df["owner"][0]
    data = dict(nav=[{"readme": "readme.md"}])
    df = df[df.dir.apply(str).str.endswith(tuple(".ipynb .md .markdown".split()))]
    for day in df.index.get_level_values("updated_at").drop_duplicates():
        this = []
        data["nav"].append({day.to_pydatetime().strftime("%D"): this})
        for path in df.loc[day].index.get_level_values(0).drop_duplicates():
            for id in df.loc[day].loc[path].index.get_level_values(0).drop_duplicates():
                g = df.loc[day].loc[path].loc[id]

                this.append(
                    {
                        g.description[0].lstrip(): [
                            {i: str(x.dir.relative_to(path))} for i, x in g.iterrows()
                        ]
                    }
                )
    return MkDocs(
        **data,
        plugins="mkdocs-jupyter".split(),
        site_name=owner["login"],
        docs_dir=owner["login"],
        site_dir="_build/html/mkdocs"
    )


class MkDocs(BaseModel):
    site_name: str
    site_description: Optional[str]
    site_url: Optional[str]
    nav: List[dict] = Field(default_factory=list)
    plugins: list = Field(default_factory=list)
    docs_dir: str = "docs"
    site_dir: str = "_build/html/mkdocs"
