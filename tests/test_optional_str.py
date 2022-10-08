from dataclasses import dataclass, field
from enum import Enum
from typing import List, Union, Optional

import yada


@dataclass
class TrainArgsOptStrNotNoneDefault:
    length_column_name: Optional[str] = field(
        default="length",
        metadata={
            "help": "Column name with precomputed lengths to use when grouping by length."
        },
    )


@dataclass
class TrainArgsOptStrNoneDefault:
    resume_from_checkpoint: Optional[str] = field(
        default=None,
        metadata={
            "help": "The path to a folder with a valid checkpoint for your model."
        },
    )


@dataclass
class TrainArgsOptStrNoneDefaultWithCustomKeywords:
    resume_from_checkpoint: Optional[str] = field(
        default=None,
        metadata={
            "help": "The path to a folder with a valid checkpoint for your model.",
            "none_keywords": ["None"],
        },
    )


@dataclass
class TrainArgsOptListStr:
    report_to: Optional[List[str]] = field(
        default=None,
        metadata={
            "help": "The list of integrations to report the results and logs to."
        },
    )


def test_optional_str_not_none_default():
    parser = yada.Parser1(TrainArgsOptStrNotNoneDefault)
    args = parser.parse_args(["--length-column-name", "abc"])
    assert args == TrainArgsOptStrNotNoneDefault("abc")
    args = parser.parse_args(["--length-column-name", "none"])
    assert args == TrainArgsOptStrNotNoneDefault(None)
    args = parser.parse_args([])
    assert args == TrainArgsOptStrNotNoneDefault("length")


def test_optional_str_none_default():
    parser = yada.Parser1(TrainArgsOptStrNoneDefault)
    args = parser.parse_args(["--resume-from-checkpoint", "ckpt2"])
    assert args == TrainArgsOptStrNoneDefault("ckpt2")
    args = parser.parse_args(["--resume-from-checkpoint", "none"])
    assert args == TrainArgsOptStrNoneDefault("none")
    args = parser.parse_args([])
    assert args == TrainArgsOptStrNoneDefault(None)


def test_optional_str_none_default_with_none_keywords():
    parser = yada.Parser1(TrainArgsOptStrNoneDefaultWithCustomKeywords)
    args = parser.parse_args(["--resume-from-checkpoint", "ckpt2"])
    assert args == TrainArgsOptStrNoneDefaultWithCustomKeywords("ckpt2")
    args = parser.parse_args(["--resume-from-checkpoint", "none"])
    assert args == TrainArgsOptStrNoneDefaultWithCustomKeywords("none")
    args = parser.parse_args([])
    assert args == TrainArgsOptStrNoneDefaultWithCustomKeywords(None)
    args = parser.parse_args(["--resume-from-checkpoint", "None"])
    assert args == TrainArgsOptStrNoneDefaultWithCustomKeywords(None)


def test_optional_lst_str():
    parser = yada.Parser1(TrainArgsOptListStr)
    args = parser.parse_args(["--report-to", "wandb", "tensorboard"])
    assert args == TrainArgsOptListStr(["wandb", "tensorboard"])
    args = parser.parse_args(["--report-to", "none"])
    assert args == TrainArgsOptListStr(["none"])
    args = parser.parse_args([])
    assert args == TrainArgsOptListStr(None)
