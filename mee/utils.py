from pathlib import Path


def main(object=None, argv=None, raises=False):
    """a generic runner for tasks in process."""

    import sys

    import doit

    if callable(object):
        object = [object]

    if argv is None:
        argv = sys.argv[1:]

    if isinstance(argv, str):
        argv = argv.split()

    main = doit.doit_cmd.DoitMain(doit.cmd_base.ModuleTaskLoader(object))

    code = main.run(argv)
    if raises:
        sys.exit(code)
    return code


def write(file, data):
    from schemata import utils

    file = Path(file)
    if file.suffix in ".yaml .yml".split():
        from ruamel_yaml import YAML

        yaml = YAML()

        if file.exists():
            data = utils.merge(yaml.load(file.read_text()), data)
        with file.open("w") as f:
            yaml.dump(data, f)

    if file.suffix in ".cfg .ini".split():
        from configupdater import ConfigUpdater

        cfg = ConfigUpdater()

        if file.exists():
            cfg.read(file)
            data = utils.merge(cfg, data)
        file.write_text(str(cfg))

    if file.suffix in ".toml".split():
        from tomlkit import parse, dumps

        if file.exists():
            data = utils.merge(parse(file.read_text()), data)
        file.write_text(dumps(data))


def read(file, suffix=None):
    file = Path(file)
    suffix = suffix or file.suffix
    if suffix in ".yaml .yml".split():
        from ruamel_yaml import YAML

        yaml = YAML()
        return yaml.load(file.read_text())
    if suffix in ".cfg .ini".split():
        from configparser import ConfigParser

        cfg = ConfigParser()
        cfg.read(file)
        return cfg
    if suffix in ".toml".split():
        from tomlkit import parse

        return parse(file.read_text())
