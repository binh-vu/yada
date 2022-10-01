# Yada

![PyPI](https://img.shields.io/pypi/v/t2-yada)
![Python](https://img.shields.io/badge/python-v3.8+-blue.svg)
[![GitHub Issues](https://img.shields.io/github/issues/binh-vu/yada.svg)](https://github.com/binh-vu/yada/issues)
![Contributions welcome](https://img.shields.io/badge/contributions-welcome-orange.svg)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://opensource.org/licenses/MIT)

Yada (**Y**et **A**nother **D**ataclass **A**rgument Parser!) is a library to automatically generate `argparse.ArgumentParser` given data classes. Compared to some available options such as: [Huggingface's HfArgumentParser](https://huggingface.co/transformers/v4.2.2/_modules/transformers/hf_argparser.html), [argparse_dataclass](https://github.com/mivade/argparse_dataclass), and [tap](https://github.com/swansonk14/typed-argument-parser), it offers the following benefits:

1. Static Type Checking
2. Nested data classes and complex types
3. Easy to extend and customize the parser
4. Generate command line arguments given the data classes.

## Installation

Install via PyPI (requires Python 3.8+):

```bash
pip install t2-yada
```

## How to use

Yada's parser can be constructed from data classes. It relies on fieds' annotated types to construct correct argument parsers.

```python
import yada
from dataclasses import dataclass
from typing import *

@dataclass
class CityArgs:
    city: Literal["LA", "NY"]


@dataclass
class NestedArgs:
    name: str
    nested: CityArgs

parser = yada.YadaParser(NestedArgs)
args = parser.parse_args()  # or use parser.parse_known_args() -- the two functions are similar to argparse.parse_args or argparse.parse_known_args
```

Note: YadaParser is annotated as a generic type: `YadaParser[C, R]` where C denotes the classes, and R denotes the instance of the classes created from the arguments. Therefore, in the above example, C is inferred as NestedArgs, but R is unknown, hence the type of `args` variable is unknown. To overcome this typing limitation, Yada provides several options for up to 10 data classes (`yada.Parser1`, `yada.Parser2`, ...). Below is two examples:

```python
parser = yada.Parser1(NestedArgs)
args = parser.parse_args()  # <-- args now has type NestedArgs
```

```python
parser = yada.Parser2((NestedArgs, CityArgs))
args = parser.parse_args()  # <-- args now has type Tuple[NestedArgs, CityArgs]
```

Note: we recommend to use one of the specific parsers `yada.Parser<N>` instead of the generic `yada.YadaParser` if possible as they provide strong typing support.

### Configuring Yada

<details>
<summary>Add help message</summary>

Yada reads the help message from the `key` property of `dataclasses.Field.metadata`

```python
import yada
from dataclasses import dataclass, field
from typing import *

@dataclass
class CityArgs:
    city: Literal["LA", "NY"] = field(metadata={"help": "city's which you want to get the timezone"})

parser = yada.Parser1(CityArgs)
```

</details>
