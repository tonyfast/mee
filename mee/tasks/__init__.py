import operator
import os
from pathlib import Path

from .. import models

if Path(".env").exists():
    import dotenv

    dotenv.load_dotenv(".env")

DOIT_CONFIG = dict(
    report="json",
    verbosity=2,
)

COLLECTOR = models.Collector()
NAME = os.getenv("GITHUB_ACTOR") or ""


class SINCE:
    params = [
        dict(
            name="name",
            short="n",
            default=os.getenv("GITHUB_ACTOR") or "",
            type=str,
        ),
        dict(name="since", short="s", default="three months ago", type=str),
    ]


def get_time(since, round="day"):
    import datetime

    import maya
    from maya import MayaDT

    time = maya.when(since)
    attrs = "year month day hour minute second microsecond".split()
    l = len(attrs)
    id = attrs.index(round) + 1
    args = operator.attrgetter(*attrs[:id])(time)
    args += tuple([0] * len(attrs[id:]))
    return MayaDT.from_datetime(
        datetime.datetime(*args, time.datetime().tzinfo)
    ).iso8601()


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
