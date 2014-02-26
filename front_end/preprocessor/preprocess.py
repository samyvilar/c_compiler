__author__ = 'samyvilar'

from itertools import chain, imap, repeat

from utils.sequences import peek
from front_end.preprocessor.directives import get_directives
from front_end.preprocessor.macros import Macros
from front_end.tokenizer.tokens import IGNORE, filter_out_empty_tokens


def _apply(token_seq, directives, macros):
    return chain.from_iterable(
        imap(apply, imap(directives.__getitem__, imap(peek, repeat(token_seq))), repeat((token_seq, macros)))
    )


def preprocess(
        token_seq=(),
        macros=None,
        directives=None,
        include_dirs=(),
        ignore_tokens=IGNORE,
):
    return filter_out_empty_tokens(
        _apply(
            iter(token_seq),
            directives or get_directives(),
            macros or Macros((('__ include_dirs __', include_dirs), ('__ preprocess __',  preprocess)))
        ),
        ignore_tokens
    )