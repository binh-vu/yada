from typing import get_origin, get_args, Generic, TypeVar
from dataclasses import dataclass

K = TypeVar("K")
V = TypeVar("V")


@dataclass
class MyPair(Generic[K, V]):
    key: K
    value: V


def test_origin():
    assert get_origin(MyPair) == None
    assert get_origin(MyPair[str, str]) == MyPair
    assert get_args(MyPair) == ()
    assert get_args(MyPair[str, str]) == (str, str)
