from pathlib import Path
from typing import List, Optional
import json
from ..models import BaseModel, Field
from .. import SETTINGS, DOIT_CONFIG, main


def get_mkdocs():

    import sqlite_utils, sqlite3, maya

    data = dict(nav=[])
    content = {}
    SETTINGS.config.initialize()
    db = sqlite_utils.Database(sqlite3.connect(SETTINGS.db))
    for name, info in SETTINGS.config.gitmodules.items():
        print(name)
        if name.startswith("submodule"):
            row = db["gist"].get(info["url"])
            content[maya.MayaDT.from_iso8601(row["created_at"])] = row

    for when in sorted(content, reverse=True):
        row = content[when]
        if not (row["description"] and row["public"]):
            continue

        data["nav"].append(
            {
                f"{when:%F}": {
                    row["description"]: [
                        str(Path(SETTINGS.name, row["id"], file))
                        for file in json.loads(row["files"])
                        if file.endswith((".md", ".markdown"))
                    ]
                }
            }
        )

    return MkDocs(
        **data,
        plugins=[],  # "mkdocs-jupyter".split(),
        site_name=SETTINGS.name,
        docs_dir=SETTINGS.name,
        site_dir="_build/html/mkdocs",
    )


class MkDocs(BaseModel):
    site_name: str
    site_description: Optional[str]
    site_url: Optional[str]
    nav: List[dict] = Field(default_factory=list)
    plugins: list = Field(default_factory=list)
    docs_dir: str = "docs"
    site_dir: str = "_build/html/mkdocs"


def task_mkdocs():
    "configure mkdocs.yml"

    def do():
        import ruamel.yaml

        Path("mkdocs.yml").write_text(
            ruamel.yaml.safe_dump(get_mkdocs().dict(), default_flow_style=False)
        )

    return dict(actions=[do], targets=["mkdocs.yml"])


if __name__ == "__main__":
    main(globals())
