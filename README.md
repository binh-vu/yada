# yada

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
