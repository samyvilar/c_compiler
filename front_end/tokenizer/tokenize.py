__author__ = 'samyvilar'

from itertools import ifilterfalse
from sequences import peek
from front_end.tokenizer.parser import get_directives
from front_end.tokenizer.tokens import IGNORE


def tokens(values, directives):
    while peek(values, default=False):
        yield directives[peek(values)](values)


def tokenize(values=(), parsing_functions=get_directives()):
    return ifilterfalse(lambda token: isinstance(token, IGNORE), tokens(values, parsing_functions))