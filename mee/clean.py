from .settings import Settings
from . import main
from doit.task import clean_targets


def task_delete_mee_database():
    return dict(
        actions=None,
        targets=[Settings.DATA_DIR / "mee.sqlite"],
        clean=[clean_targets],
    )


if __name__ == "__main__":
    main(globals())
