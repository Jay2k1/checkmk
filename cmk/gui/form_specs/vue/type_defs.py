from dataclasses import dataclass
from enum import auto, Enum
from typing import Any

DataForDisk = Any
Value = Any


class DEFAULT_VALUE:
    pass


default_value = DEFAULT_VALUE()


class DataOrigin(Enum):
    DISK = auto()
    FRONTEND = auto()


@dataclass
class VisitorOptions:
    # Depending on the origin, we will call the migrate function
    data_origin: DataOrigin
