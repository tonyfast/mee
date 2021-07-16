from .. import models


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
    return models.Toc(**toc)


def get_config(df):
    owner = df["owner"][0]
    return models.Config(
        name=owner["login"], title=owner["login"], logo=owner["avatar_url"]
    )
