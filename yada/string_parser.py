import argparse
from typing import Callable, Optional, Set, Tuple, Union

from yada.argname import ArgumentName


class StringParser:
    """Provides different parsing method (argparse.Argument's type) to convert arg string to the desired type."""

    def __init__(self, argname: Union[str, ArgumentName]):
        self.argname = argname

    def bool(self, v: str) -> bool:
        """Parsing a boolean value"""
        if v.lower() in ("yes", "true", "t", "y", "1"):
            return True
        elif v.lower() in ("no", "false", "f", "n", "0"):
            return False
        raise argparse.ArgumentTypeError(
            f"{self._get_argname()} expects a truthy value (one of yes/no, true/false, t/f, y/n, 1/0 (case insensitive)), but got {v}"
        )

    def empty_or_none(self, v: str) -> Optional[str]:
        """Parsing a value that must be either empty string or None"""
        if v in ("None", "none"):
            return None
        if v == "":
            return ""

        raise argparse.ArgumentTypeError(
            f"{self._get_argname()} expects an empty string or None/none value but got {v}"
        )

    def literal(self, v: str) -> Union[int, str, None]:
        """Parsing a literal value used in typing.Literal arguments"""
        if v in ("None", "none"):
            return None
        if v.isdigit():
            return int(v)
        if v.lower() in ("yes", "true", "t", "y", "1"):
            return True
        if v.lower() in ("no", "false", "f", "n", "0"):
            return False
        return v

    @staticmethod
    def wrap_nullable(
        fn: Callable, none_keywords: Union[Set[str], Tuple[str, ...]] = ("None", "none")
    ):
        def wrapper(s):
            if s in none_keywords:
                return None
            return fn(s)

        return wrapper

    def _get_argname(self):
        if isinstance(self.argname, str):
            return self.argname
        return self.argname.get_argname()
