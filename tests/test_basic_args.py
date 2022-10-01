from dataclasses import dataclass

import yada


@dataclass
class BasicArgs:
    integer: int
    string: str
    _float: float


def test_basic_dataclass():
    parser = yada.Parser1(BasicArgs)
    args = parser.parse_args(
        [
            "--integer",
            "10",
            "--string",
            "hello",
            "--_float",
            "10.4",
        ]
    )
    assert args == BasicArgs(10, "hello", 10.4)
