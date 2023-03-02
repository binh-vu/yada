from __future__ import annotations
import argparse
from functools import partial
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Literal,
    Optional,
    Sequence,
    Tuple,
    Type,
    Union,
    get_args,
    get_origin,
    get_type_hints,
    Generic,
    TypeVar,
)
from dataclasses import MISSING, Field, fields, is_dataclass, Field
from yada.string_parser import StringParser
from yada.ns_parser import (
    MultiFieldParser,
    SingleFieldParser,
    NamespaceParser,
)
import collections.abc as abc
from yada.exceptions import NotSupportedType
from loguru import logger
import argparse
from dataclasses import is_dataclass
from yada.argname import ArgumentName

C = TypeVar("C")
R = TypeVar("R")
NoneType = type(None)


class YadaParser(Generic[C, R]):
    """Parsing parameters defined by one or multiple dataclass.

    Some important behaviors:

    - Parameter declared as union:
        * only support mixed of primitive types, or one optional complex type.
        * optional complex type should not be confused with default value, because an optional parameter can have a default value different than None.
        * when we have one optional complex type, to specify that complex type is None, we introduce a new
            cmd argument `--<param_name> none` to specify when it is None. All other fields of this complex
            type must be optional as users may want to specify only a subset of the fields.
    - Complex parameter can have a default value:
        * when a nested parameter such as MethodArgs have a default value, a default value can be different
            from the MethodArgs field's default value, so the generated cmd argument need to set the default value
            correctly.
        * when a user override some default value by providing it, it should not affect how the default value we
            set previously using the rule above.
    - Parameter declared as list or set:
        * because we are using nargs to parse, we cannot generate nested argument for complex type, therefore, if
            a parameter is a complex type, it must be able to be parsed from a string. Use `type_constructors` or
            `field_constructors` to provide a custom constructor in this case.
    - Parameter declared as a dictionary:
        * passing a dictionary is not cmd friendly, since we do not know the key, we cannot generate nested arguments
            to parse the type correctly. Therefore, the dictionary must be able to reconstructed from a string. Use
            `type_constructors` or `field_constructors` to provide a custom constructor in this case.

    Some useful metadata of a field (provided by field={'metadata': {}}) that YadaParser understands:
        - help: for displaying help message
        - none_keywords: list of tokens that are considered equivalent to None
        - parser: a function that takes a string and return an instance of the field's type. This is similar to
            `field_parsers`. Note that for list, it takes a string for each item in the list.

    Args:
        classes: one or more classes holding parameters. Properties of each class will be converted to arguments.
            When params is a sequence of classes, the properties of all classes will be in the same namespace.
            When params is a mapping of key and classes, the key will act as the namespace and the arguments will
            be prefixed with the key and the dot character.

        dash: whether to convert underscore to dash in the argument name.

        levelsep: the separator used to separate nested argument (default is `.`).

        type_parsers: a mapping of type to a function that takes a string and return an instance of that type.
            This is useful when the type's constructor cannot be constructed from a string, for example, a dataclass of
            more than one field

        field_parsers: a mapping of a nested field (separated by dot) to a function that takes a string and
            return an instance of the field's type.

        namespaces: a sequence of namespaces for each corresponding class (by position), only used when classes is a sequence. This has the same affect
            as when classes is a mapping of key and classes, but is more friendly to type hinting. If a namespace is empty, it won't be used to scope
            the corresponding class.
    """

    def __init__(
        self,
        classes: C,
        dash: bool = True,
        levelsep: str = ".",
        type_parsers: Optional[Dict[Type, Callable[[str], Type]]] = None,
        field_parsers: Optional[Dict[str, Callable[[str], Type]]] = None,
        namespaces: Optional[Sequence[str]] = None,
    ):
        self.classes = classes
        self.dash = dash
        self.levelsep = levelsep
        self.parser = argparse.ArgumentParser()
        self.type_parsers = type_parsers or {}
        self.field_parsers = field_parsers or {}

        self.value_parser: Union[
            Dict[str, NamespaceParser], List[NamespaceParser], NamespaceParser
        ]
        argname = ArgumentName(dclass=None, names=[], dash=dash, levelsep=levelsep)
        if is_dataclass(classes):
            argname.dclass = classes
            self.value_parser = self.add_dataclass(classes, argname)
        elif isinstance(classes, (list, tuple)):
            self.value_parser = []
            for i, dclass in enumerate(classes):
                argname.dclass = dclass
                if namespaces is not None and namespaces[i] != "":
                    dargname = argname.add(namespaces[i])
                else:
                    dargname = argname
                self.value_parser.append(self.add_dataclass(dclass, dargname))
        elif isinstance(classes, dict):
            self.value_parser = {}
            for namespace, dclass in classes.items():
                argname.dclass = dclass
                self.value_parser[namespace] = self.add_dataclass(
                    dclass, argname.add(namespace)
                )

    def parse_args(self, args: Optional[Sequence[str]] = None) -> R:
        ns = self.parser.parse_args(args)

        if isinstance(self.value_parser, dict):
            return {k: v.deserialize(ns) for k, v in self.value_parser.items()}  # type: ignore
        elif isinstance(self.value_parser, list):
            return [v.deserialize(ns) for v in self.value_parser]  # type: ignore
        else:
            return self.value_parser.deserialize(ns)  # type: ignore

    def parse_known_args(
        self, args: Optional[Sequence[str]] = None
    ) -> Tuple[R, List[str]]:
        ns, remain_args = self.parser.parse_known_args(args)

        if isinstance(self.value_parser, dict):
            return {k: v.deserialize(ns) for k, v in self.value_parser.items()}, remain_args  # type: ignore
        elif isinstance(self.value_parser, list):
            return [v.deserialize(ns) for v in self.value_parser], remain_args  # type: ignore
        else:
            return self.value_parser.deserialize(ns), remain_args  # type: ignore

    def add_dataclass(
        self,
        dclass,
        argname: ArgumentName,
        default: Any = MISSING,
        default_factory: Union[Any, Callable[[], Any]] = MISSING,
        is_nullable: bool = False,
    ) -> NamespaceParser:
        """Generate arguments from a dataclass

        Args:
            dclass: the dataclass type
            argname: argument name
            default: the default value of the dataclass
            default_factory: the default factory of the dataclass
            is_nullable: whether the dataclass is nullable
        """
        type_hints: Dict[str, type] = get_type_hints(dclass)

        if default is not MISSING:
            default_instance = default
        elif default_factory is not MISSING:
            default_instance = default_factory()
        else:
            default_instance = None

        deser = MultiFieldParser(
            type=dclass,
            field_parsers={},
            is_default_null=default_instance is None,
            is_nullable=is_nullable,
            null_argname=argname.get_fieldname(),
        )

        if is_nullable:
            self.parser.add_argument(
                argname.get_argname(),
                type=StringParser(argname).empty_or_none,
                default="",
                required=False,
            )

        for field in fields(dclass):
            if not field.init:
                logger.trace(
                    "Only fields with init=True are supported (included in the generated __init__ method). Skipping field: {} in {}"
                    ".".join(argname.names),
                    dclass.__qualname__,
                )
                continue

            field_argname = argname.add(field.name)
            field_type = type_hints[field.name]

            field_default = field.default
            if default_instance is not None:
                # we have the default value, which may set different value from the field's default value
                # so it has higher priority
                field_default = getattr(default_instance, field.name)
            elif field_default is MISSING and field.default_factory is not MISSING:
                field_default = field.default_factory()
            field_required = field_default is MISSING and not is_nullable

            deser.field_parsers[field.name] = self.add_field(
                field_argname,
                field,
                field_type,
                is_required=field_required,
                default_value=field_default,
            )

        return deser

    def add_field(
        self,
        argname: ArgumentName,
        field: Field,
        field_type: type,
        is_required: bool,
        default_value: Any,
    ) -> NamespaceParser:
        origin_field_type = field_type
        origin = get_origin(field_type)
        args = get_args(field_type)

        # detect Optional[T] to set nullable to True
        # then we convert field type from Optional[T] to T and process as normal
        if origin is Union:
            if any(arg is NoneType for arg in args):
                args = [arg for arg in args if arg is not NoneType]
                is_nullable = True

                if len(args) == 1:
                    # Optional[T] -> T
                    field_type = args[0]
                    origin = get_origin(field_type)
                    args = get_args(field_type)
            else:
                is_nullable = False
        else:
            is_nullable = False

        if origin is Union:
            all_str_args = True
            for arg in args:
                try:
                    if not issubclass(arg, str):
                        all_str_args = False
                        break
                except TypeError:
                    all_str_args = False
                    break

            if all_str_args:
                # handle special case of Union[StrEnum, str]
                is_nullable = False
                field_type = str
            else:
                raise NotSupportedType(
                    argname,
                    origin_field_type,
                    "only `Union[X, NoneType]` (i.e., `Optional[X]`) is allowed for `Union` because"
                    " we don't know how to parse different types from string.",
                )
            self.parser.add_argument(
                argname.get_argname(),
                **self.get_add_argument_options(
                    argname, field, field_type, default_value, is_required, is_nullable
                ),
            )
            return SingleFieldParser(
                argname.get_fieldname(), default_value=default_value
            )

        if origin is None or origin is Literal:
            # not generic types
            if is_dataclass(field_type):
                return self.add_dataclass(
                    field_type,
                    argname,
                    default=default_value,
                    is_nullable=is_nullable,
                )

            # we assume it can be reconstructed from string
            # some classes support this is enum.Enum, pathlib.Path
            # TODO: raise an error if the class doesn't allow to construct from string
            self.parser.add_argument(
                argname.get_argname(),
                **self.get_add_argument_options(
                    argname, field, field_type, default_value, is_required, is_nullable
                ),
            )
            return SingleFieldParser(
                argname.get_fieldname(), default_value=default_value
            )

        if origin is list or origin is set or origin is abc.Sequence:
            assert len(args) == 1
            self.parser.add_argument(
                argname.get_argname(),
                nargs="*",
                **self.get_add_argument_options(
                    argname,
                    field,
                    args[0],
                    default_value,
                    is_required,
                    is_nullable=False,
                ),
            )
            if origin is set:
                return SingleFieldParser(
                    argname.get_fieldname(),
                    default_value=default_value,
                    postprocess=set,
                )
            return SingleFieldParser(
                argname.get_fieldname(), default_value=default_value
            )

        if origin is dict:
            self.parser.add_argument(
                argname.get_argname(),
                **self.get_add_argument_options(
                    argname,
                    field,
                    field_type,
                    default_value,
                    is_required,
                    is_nullable=False,
                ),
            )
            return SingleFieldParser(
                argname.get_fieldname(), default_value=default_value
            )

        raise NotSupportedType(argname, field_type)

    def get_add_argument_options(
        self,
        argname: ArgumentName,
        field: Field,
        field_type: type,
        default_value: Any,
        is_required: bool,
        is_nullable: bool,
    ) -> dict:
        if is_nullable:
            if field_type is str:
                # for a string, we do not know if the value can contain "None" or "none"
                # - if the default value is None, then at least user can choose None if
                #   they don't pass the argument
                # - if the default value is not None, then we need to have a way to
                #   distinguish between None and "None" or "none"
                if default_value is None and "none_keywords" not in field.metadata:
                    wrapper = lambda x: x
                else:
                    if "none_keywords" not in field.metadata:
                        # force to use "None" or "none" as users has no way to specify None
                        wrapper = StringParser.wrap_nullable
                    else:
                        wrapper = partial(
                            StringParser.wrap_nullable,
                            none_keywords=set(field.metadata["none_keywords"]),
                        )
            else:
                wrapper = StringParser.wrap_nullable
        else:
            wrapper = lambda x: x

        options = {
            "default": MISSING,
            "required": is_required,
            "help": field.metadata.get("help", ""),
        }
        if field_type is bool:
            options["type"] = StringParser(argname).bool
        elif field_type in self.type_parsers:
            options["type"] = wrapper(self.type_parsers.get(field_type, field_type))
        elif argname in self.field_parsers:
            options["type"] = wrapper(self.field_parsers.get(argname, field_type))
        elif "parser" in field.metadata:
            options["type"] = wrapper(field.metadata["parser"])
        else:
            origin = get_origin(field_type)
            if origin is Literal:
                args = get_args(field_type)
                # Note: inclusion in the choices container is checked after any type conversions have been performed
                # https://docs.python.org/3/library/argparse.html#choices
                arg_types = list({type(arg) for arg in args})
                if len(arg_types) == 1:
                    field_type_parser = arg_types[0]
                else:
                    field_type_parser = StringParser(argname).literal
                options["choices"] = args
                options["type"] = wrapper(field_type_parser)
            else:
                options["type"] = wrapper(field_type)
        return options


R1 = TypeVar("R1")
R2 = TypeVar("R2")
R3 = TypeVar("R3")
R4 = TypeVar("R4")
R5 = TypeVar("R5")
R6 = TypeVar("R6")
R7 = TypeVar("R7")
R8 = TypeVar("R8")
R9 = TypeVar("R9")
R10 = TypeVar("R10")


class Parser1(YadaParser[Type[R1], R1]):
    pass


class Parser2(YadaParser[Tuple[Type[R1], Type[R2]], Tuple[R1, R2]]):
    pass


class Parser3(YadaParser[Tuple[Type[R1], Type[R2], Type[R3]], Tuple[R1, R2, R3]]):
    pass


class Parser4(
    YadaParser[Tuple[Type[R1], Type[R2], Type[R3], Type[R4]], Tuple[R1, R2, R3, R4]]
):
    pass


class Parser5(
    YadaParser[
        Tuple[Type[R1], Type[R2], Type[R3], Type[R4], Type[R5]],
        Tuple[R1, R2, R3, R4, R5],
    ]
):
    pass


class Parser6(
    YadaParser[
        Tuple[Type[R1], Type[R2], Type[R3], Type[R4], Type[R5], Type[R6]],
        Tuple[R1, R2, R3, R4, R5, R6],
    ]
):
    pass


class Parser7(
    YadaParser[
        Tuple[Type[R1], Type[R2], Type[R3], Type[R4], Type[R5], Type[R6], Type[R7]],
        Tuple[R1, R2, R3, R4, R5, R6, R7],
    ]
):
    pass


class Parser8(
    YadaParser[
        Tuple[
            Type[R1],
            Type[R2],
            Type[R3],
            Type[R4],
            Type[R5],
            Type[R6],
            Type[R7],
            Type[R8],
        ],
        Tuple[R1, R2, R3, R4, R5, R6, R7, R8],
    ]
):
    pass


class Parser9(
    YadaParser[
        Tuple[
            Type[R1],
            Type[R2],
            Type[R3],
            Type[R4],
            Type[R5],
            Type[R6],
            Type[R7],
            Type[R8],
            Type[R9],
        ],
        Tuple[R1, R2, R3, R4, R5, R6, R7, R8, R9],
    ]
):
    pass


class Parser10(
    YadaParser[
        Tuple[
            Type[R1],
            Type[R2],
            Type[R3],
            Type[R4],
            Type[R5],
            Type[R6],
            Type[R7],
            Type[R8],
            Type[R9],
            Type[R10],
        ],
        Tuple[R1, R2, R3, R4, R5, R6, R7, R8, R9, R10],
    ]
):
    pass
