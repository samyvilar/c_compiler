__author__ = 'samyvilar'

from utils.sequences import peek
from front_end.tokenizer.parser import get_directives
from front_end.tokenizer.tokens import filter_out_empty_tokens, IGNORE

from itertools import repeat, imap


def tokens(values, directives):
    return imap(apply, imap(directives.__getitem__, imap(peek, repeat(values))), repeat((values,)))


def tokenize(values=(), parsing_functions=get_directives(), ignore_tokens=IGNORE):
    return filter_out_empty_tokens(tokens(iter(values), parsing_functions), ignore_tokens)