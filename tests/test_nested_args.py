from dataclasses import dataclass
from typing import Literal

import yada


@dataclass
class CityArgs:
    city: Literal["LA", "NY"]


@dataclass
class NestedArgs:
    name: str
    nested: CityArgs


def test_nested_dataclass():
    parser = yada.Parser1(NestedArgs)
    args = parser.parse_args(
        [
            "--name",
            "hello",
            "--nested.city",
            "NY",
        ]
    )
    assert args == NestedArgs("hello", CityArgs("NY"))
