from dataclasses import dataclass, field
from typing import Union
from yada.yada import YadaParser
from enum import Enum


class IntervalStrategy(str, Enum):
    NO = "no"
    STEPS = "steps"
    EPOCH = "epoch"


@dataclass
class TrainingArguments:
    strategy: Union[IntervalStrategy, str] = field(
        default="no",
        metadata={"help": "The evaluation strategy to use."},
    )


def test_mixed_enum_str():
    """Testing to make sure it is compatible with huggingface HfArgumentParser"""
    parser = YadaParser(TrainingArguments)
    args = parser.parse_args(
        [
            "--strategy",
            "epoch",
        ]
    )
    assert args == TrainingArguments(IntervalStrategy.EPOCH)
