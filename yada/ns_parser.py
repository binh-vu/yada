from abc import ABC, abstractmethod
import argparse
from dataclasses import MISSING, dataclass
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Type,
)


class NamespaceParser(ABC):
    @abstractmethod
    def deserialize(self, ns: argparse.Namespace):
        pass

    @abstractmethod
    def is_presented(self, ns: argparse.Namespace):
        pass


@dataclass
class SingleFieldParser(NamespaceParser):
    field_name: str
    default_value: Any
    postprocess: Callable[[Any], Any] = lambda x: x

    def deserialize(self, ns: argparse.Namespace):
        value = getattr(ns, self.field_name.replace("-", "_"))
        if value is MISSING:
            value = self.default_value
        return self.postprocess(value)

    def is_presented(self, ns: argparse.Namespace):
        return getattr(ns, self.field_name.replace("-", "_")) is not MISSING


@dataclass
class MultiFieldParser(NamespaceParser):
    type: Type
    field_parsers: Dict[str, NamespaceParser]
    is_default_null: bool
    is_nullable: bool
    null_argname: str

    def deserialize(self, ns: argparse.Namespace):
        """Deserialize a dataclass.

        1. When the dataclass is not nested, we will have:
            - required = true
            - is_nullable = False
            and values of all fields must be present in the namespace unless the field is optional (having a default value not MISSING).
        2. When the dataclass is nested, we may have:
            (A) the parent field is X, then is_nullable = False
                - if it has default value, then required = False, all fields are optional and have a default value be X.default.field
                - if it doesn't have a default value, then required = True, it is the same as when the dataclass is not nested.
                Because of the current implementation that the default value of the field is already taken into account the default value of
                the parent class, we don't need branching in 2.A
            (B) the parent field has type Optional[X], but have no default value
                then is_nullable = True, required = True, all fields are optional (because if you require them, you cannot set just null_argname)
                - if null_argname presents, then it will be None
                - if null_argname does not present,
                    + when users provide values of some field, then the value of this class is not None.
                    + when users do not provide any values for the field, we must check if users provide any value
                        for the fields of X. If they don't, then the value of this class is None, otherwise it is an instance of X.
            (C) the parent field has type Optional[X], but have a default value (it will be not None, otherwise it is case B, shown later)
                then is_nullable = True, required = False, all fields are optional (because if you require them, you cannot set just null_argname)
                - if null_argname presents, then it will be None
                - if null_argname does not present,
                    + when users provide values of some field, then the value of this class is not None.
                    + when users do not provide any values for the field, then the value of this class is the default value (which is case 2.A). This mean, if the default
                        value is None, then (B) and (C) are the same, so we assume that the default value is always not None. Which means, this is reduced to 2.A

        Case 1 is equivalent to 2.A. We only need to distinguish between 2.A and 2.B/C, we can do it via `is_nullable`.
        """
        if not self.is_nullable:
            # case 1 or 2.A
            obj = {}
            for fname, f in self.field_parsers.items():
                value = f.deserialize(ns)
                obj[fname] = value
            return self.type(**obj)

        if getattr(ns, self.null_argname) is None:
            # null_argname is presented, then the value is None
            return None

        # distinguish between 2.B and 2.C
        if not self.is_default_null:
            # case 2.C
            obj = {}
            for name, f in self.field_parsers.items():
                value = f.deserialize(ns)
                obj[name] = value
            return self.type(**obj)

        # case 2.B
        obj = {}
        if all(not f.is_presented(ns) for f in self.field_parsers.values()):
            return None

        for fname, f in self.field_parsers.items():
            value = f.deserialize(ns)
            obj[fname] = value
        return self.type(**obj)

    def is_presented(self, ns: argparse.Namespace):
        return any(f.is_presented(ns) for f in self.field_parsers.values())
