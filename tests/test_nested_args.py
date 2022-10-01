from dataclasses import dataclass
from typing import Literal

from yada.yada import YadaParser


@dataclass
class CityArgs:
    city: Literal["LA", "NY"]


@dataclass
class NestedArgs:
    name: str
    nested: CityArgs


def test_nested_dataclass():
    parser = YadaParser(NestedArgs)
    args = parser.parse_args(
        [
            "--name",
            "hello",
            "--nested.city",
            "NY",
        ]
    )
    assert args == NestedArgs("hello", CityArgs("NY"))
