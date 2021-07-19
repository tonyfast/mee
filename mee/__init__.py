"a decentralized publishing system based on git and github"
import datetime, sys

__version__ = datetime.date.today().strftime("%Y.%M.%d.%H")


from .tools import *
from .settings import Settings

SETTINGS = Settings()
DOIT_CONFIG = SETTINGS.DOIT_CONFIG
