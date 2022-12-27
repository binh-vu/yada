from argparse import ArgumentError
import pytest
from dataclasses import dataclass
from yada import Parser2, YadaParser


@dataclass
class Arg1:
    topk: int = 1


@dataclass
class Arg2:
    topk: int = 2


@dataclass
class Arg3:
    er_topk: int = 3


def test_parse_seq():
    # parsing dataclasses that do not have overlapping fields
    arg1, arg3 = Parser2((Arg1, Arg3)).parse_args(["--topk", "10", "--er-topk", "20"])
    assert arg1 == Arg1(10)
    assert arg3 == Arg3(20)

    # parsing dataclasses that have overlapping fields will raise an error
    with pytest.raises(ArgumentError):
        parser = Parser2((Arg1, Arg2))

    # unless they are prefixed with namespaces
    arg1, arg2 = Parser2((Arg1, Arg2), namespaces=["", "a2"]).parse_args(
        ["--topk", "10", "--a2.topk", "20"]
    )
    assert arg1 == Arg1(10)
    assert arg2 == Arg2(20)


def test_parse_map():
    # parsing dataclasses that do not have overlapping fields
    out = YadaParser({"a1": Arg1, "a3": Arg3}).parse_args(
        ["--a1.topk", "10", "--a3.er-topk", "20"]
    )
    assert out["a1"] == Arg1(10)
    assert out["a3"] == Arg3(20)

    # parsing dataclasses that have overlapping fields
    out = YadaParser({"a1": Arg1, "a2": Arg2}).parse_args(
        ["--a1.topk", "10", "--a2.topk", "20"]
    )
    assert out["a1"] == Arg1(10)
    assert out["a2"] == Arg2(20)
