__author__ = 'samyvilar'

from itertools import ifilterfalse

from sequences import peek
from front_end.preprocessor.directives import get_directives
from front_end.preprocessor.macros import Macros
from front_end.tokenizer.tokens import IGNORE


def _apply(token_seq, directives, macros):
    while peek(token_seq, default=False):
        for token in directives[peek(token_seq)](token_seq, macros, preprocess):
            yield token


def preprocess(token_seq=(), directives=None, macros=None):
    return ifilterfalse(
        lambda token: isinstance(token, IGNORE),
       _apply(token_seq, directives or get_directives(), macros or Macros())
    )