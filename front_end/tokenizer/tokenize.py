__author__ = 'samyvilar'

from itertools import ifilterfalse
from utils.sequences import peek
from front_end.tokenizer.parser import get_directives
from front_end.tokenizer.tokens import IGNORE


def tokens(values, directives):
    while True:
        yield directives[peek(values)](values)


def tokenize(values=(), parsing_functions=get_directives(), ignore_tokens=IGNORE):
    return ifilterfalse(lambda token: isinstance(token, ignore_tokens), tokens(iter(values), parsing_functions))