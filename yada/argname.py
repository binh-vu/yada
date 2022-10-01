from __future__ import annotations
from typing import List


class ArgumentName:
    """Naming convention for argparse arguments"""

    def __init__(
        self, dclass, names: List[str], dash: bool = True, levelsep: str = "."
    ):
        self.dclass = dclass
        self.names = names
        self.dash = dash
        self.levelsep = levelsep

    def add(self, name: str) -> ArgumentName:
        return ArgumentName(self.dclass, self.names + [name], self.dash, self.levelsep)

    def get_argname(self) -> str:
        return "--" + self.levelsep.join((self._norm_name(name) for name in self.names))

    def get_fieldname(self) -> str:
        return self.levelsep.join(self.names)

    def _norm_name(self, name: str):
        if self.dash:
            if name[0].startswith("_"):
                return "_" + name[1:].replace("_", "-")
            return name.replace("_", "-")
        return name
