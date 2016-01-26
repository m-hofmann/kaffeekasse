from enum import Enum


class AutoNumber(Enum):
    """
    Automatically numbered enum for python, see
    https://docs.python.org/3/library/enum.html#autonumber
    """
    def __new__(cls):
        value = len(cls.__members__) + 1
        obj = object.__new__(cls)
        obj._value = value
        return obj