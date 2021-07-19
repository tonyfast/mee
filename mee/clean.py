from . import SETTINGS
from . import main
from doit.task import clean_targets


def task_delete_mee_database():
    return dict(
        actions=None,
        targets=[SETTINGS.data_dir / "mee.sqlite"],
        clean=[clean_targets],
    )


if __name__ == "__main__":
    main(globals())
