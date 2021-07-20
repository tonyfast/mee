from ..models import BaseModel
from .. import SETTINGS, main

from pathlib import Path
import json


class NikolaMetadata(BaseModel):
    category: str = ""
    date: str = ""
    description: str = ""
    link: str = ""
    slug: str = ""
    tags: str = ""
    title: str = ""
    type: str = "text"


def enrich_metadata(path, row):
    import maya

    metadata = NikolaMetadata(
        date=format(
            maya.MayaDT.from_iso8601(row["created_at"]),
            "%Y-%m-%d %X %Z-04:00",
        ),
        name=str(path),
        title=str(path),
        slug=path.stem.replace(" ", "-"),
    )
    if path.suffix == ".ipynb":

        data = json.loads(path.read_text())
        data["metadata"].update(nikola=metadata.dict())
        path.write_text(json.dumps(data))

    if path.suffix == ".md":
        md = path.read_text()
        if md.startswith("---"):
            md = md.partition("---")[2].partition("---")[2].lstrip()

        import ruamel.yaml

        path.write_text(
            f"""---\n{ruamel.yaml.safe_dump(metadata.dict(), default_flow_style=False)}\n---\n\n{md}"""
        )


def task_nikola():
    import sqlite_utils, sqlite3, maya, json

    SETTINGS.config.initialize()
    db = sqlite_utils.Database(sqlite3.connect(SETTINGS.db))
    for row in db["gist"].rows:
        if not row["description"]:
            continue
        if not row["public"]:
            continue

        for file in json.loads(row["files"]):
            path = Path(SETTINGS.name, row["id"], file)
            if path.suffix not in (".md", ".ipynb"):
                continue
                # add support for other files later

            yield dict(
                name=f"enrich-{str(path)}",
                actions=[(enrich_metadata, [path, row])],
                targets=[path],
            )


if __name__ == "__main__":
    main(globals())
