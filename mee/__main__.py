import sys
from pathlib import Path

import typer

context_settings = dict(allow_extra_args=True, ignore_unknown_options=True)
main = typer.Typer(add_completion=False, help="mee is a tool to manage your entropy")
tasks = typer.Typer(name="tasks", help="doit file tasks")
main.add_typer(tasks)


@tasks.command(context_settings=context_settings)
def config(ctx: typer.Context):
    from .tasks import config, main

    sys.argv = sys.argv[:1] + (ctx.args or ["list"])
    main(vars(config))


@tasks.command(context_settings=context_settings)
def build(ctx: typer.Context):
    """tasks to build documentations and artifacts"""
    from .tasks import build, main

    sys.argv = sys.argv[:1] + (ctx.args or ["list"])
    main(vars(build))


@main.command(context_settings=context_settings)
def sessions(ctx: typer.Context, name: str):
    now = Path().absolute()
    runner = Path(__file__).parent / "sessions.py"
    args = []
    inner = ["-f", str(runner)]
    extra = [str(now), name]

    for arg in ctx.args:
        args.append(arg)
        if arg == "--":
            arg.extend(extra + ctx.args[len(args) :])
            break
    else:
        args.append("--")
        args.extend(extra)

    sys.argv = sys.argv[:1] + inner + args
    from nox.__main__ import main

    main()


if __name__ == "__main__":
    app()
