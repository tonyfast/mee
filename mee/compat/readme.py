def get_readme(df):
    owner = df["owner"][0]

    body = f"""# {owner["login"]}
    """
    df = df[df.dir.apply(str).str.endswith(tuple(".ipynb .md .markdown".split()))]
    for day in df.index.get_level_values("updated_at").drop_duplicates():
        s = day.to_pydatetime().strftime("%D")
        body += f"""
        
## {s}

"""

        for path in df.loc[day].index.get_level_values(0).drop_duplicates():
            for id in df.loc[day].loc[path].index.get_level_values(0).drop_duplicates():
                g = df.loc[day].loc[path].loc[id]

                body += f"""
> {g.description[0].lstrip()}
    
"""
                for i, x in g.iterrows():
                    body += f"""* {i}
"""
                else:
                    body += """
---
"""
    return body
