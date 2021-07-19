import collections
import datetime
import enum
import json
import operator
from enum import Enum
from functools import partial
from pathlib import Path
from typing import Any, ForwardRef, List, Optional, Union

from pydantic import AnyUrl, BaseModel, Field
from pydantic.types import FilePath

from . import tools

DOIT_CONFIG = dict(verbosity=2)


def get_url(url):
    import requests
    import requests_cache

    requests_cache.install_cache(".mee")
    return requests.get(url)


class Markdown(str):
    def _repr_markdown_(self):
        return self


class BaseModel(BaseModel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if hasattr(self, "__post_init__"):
            self.__post_init__()


class NonNull(BaseModel):
    def dict(self, *args, **kwargs):
        return {k: v for k, v in super().dict(*args, **kwargs).items() if v is not None}
