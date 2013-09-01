__author__ = 'samyvilar'

from itertools import ifilterfalse

from sequences import peek, terminal
from front_end.preprocessor.directives import get_directives
from front_end.preprocessor.macros import Macros
from front_end.tokenizer.tokens import IGNORE


def _apply(token_seq, directives, macros, include_dirs, takewhile, ignore_tokens):
    while takewhile(token_seq):
        for token in directives[peek(token_seq)](
                token_seq,
                macros,
                lambda tokens, ignore_tokens=ignore_tokens, **kwargs:
                preprocess(tokens, ignore_tokens=ignore_tokens, **kwargs),
                include_dirs
        ):
            yield token


def preprocess(
        token_seq=(),
        directives=None,
        macros=None,
        include_dirs=(),
        takewhile=lambda token_seq: peek(token_seq, terminal) is not terminal,
        ignore_tokens=IGNORE,
):
    return ifilterfalse(
        lambda token: isinstance(token, IGNORE),
        _apply(
            iter(token_seq), directives or get_directives(), macros or Macros(), include_dirs, takewhile, ignore_tokens
        )
    )


