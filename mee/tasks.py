from . import collector, utils
import os, json

DOIT_CONFIG = dict(
    report="json",
    verbosity=2,
)


def task_start():
    """update current gist information from the github api"""

    def update(name, since):
        global self
        self = collector.Collector(since=since)
        if not self.name:
            assert False, "name is required for development"
        self.prior()
        import json

        (self.path / "gists.json").write_text(
            json.dumps(
                self.gists[self.gists.description.astype(bool)]
                .files.apply(list)
                .to_dict()
            )
        )

    return dict(
        actions=[update],
        targets=["gists.json"],
        params=[
            dict(
                name="name",
                short="n",
                default=os.getenv("GITHUB_ACTOR") or "",
                type=str,
            ),
            dict(name="since", short="s", default="one month ago", type=str),
        ],
    )


def task_submodules():
    """update on disk submodules"""

    def update():
        import git

        global self
        for k, v in json.loads((self.path / "gists.json").read_text()).items():
            to = self.path / self.name
            to.mkdir(exist_ok=True, parents=True)
            to /= k.rpartition("/")[2]
            try:
                self.repo.git.execute(f"""git submodule add {k} {to}""".split())
            except git.GitCommandError:
                self.repo.git.execute(f"""git submodule add --force {k} {to}""".split())

    return dict(file_dep=["gists.json"], actions=[update])


def task_jb():
    """write the jupyter book configuration files"""

    def export_toc():
        global self
        self.post()
        utils.write("toc.yml", models.Toc(**self.get_toc()).dict())

    def export_config():
        global self
        utils.write("config.yml", self.get_jb_config().dict())

    return dict(
        file_dep=[".gitmodules"],
        task_dep=["submodules"],
        actions=[export_toc, export_config],
        targets=["toc.yml", "config.yml"],
    )


def task_conf_py():
    """write the sphinx conf.py file"""
    return dict(
        actions=["jb config sphinx --toc toc.yml --config config.yml . > conf.py"],
        file_dep=["toc.yml", "config.yml"],
        targets=["conf.py"],
    )


def task_sphinx():
    """build the sphinx documentation"""
    return dict(
        actions=["sphinx-build . _build/html/"],
        targets=["_build/html/index.html"],
        file_dep=["conf.py"],
    )


def task_readme():
    """create a readme summary for your works"""

    def export():
        global self
        self.post()
        (self.path / "readme.md").write_text(self.get_readme())

    return dict(actions=[export], targets=["readme.md"], task_dep=["submodules"])


if __name__ == "__main__":
    utils.main(globals())
