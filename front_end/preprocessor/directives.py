__author__ = 'samyvilar'

import os
from collections import defaultdict
from itertools import chain

from utils.sequences import peek, consume, takewhile
from front_end.preprocessor import logger
from front_end.preprocessor.conditional import if_block
from front_end.loader.load import load
from front_end.tokenizer.tokenize import tokenize
from front_end.tokenizer.parser import get_line
from front_end.tokenizer.tokens import TOKENS, STRING, IDENTIFIER, IGNORE, KEYWORD
from front_end.loader.locations import loc, EOFLocation
from front_end.preprocessor.macros import ObjectMacro, FunctionMacro
from front_end.errors import error_if_not_type, error_if_not_value, error_if_not_empty


def INCLUDE(token_seq, macros, preprocess, include_dirs):
    line = get_line(token_seq)
    _ = consume(line)
    search_paths = (os.getcwd(),)
    if isinstance(peek(line, None), STRING):
        file_path = consume(line)
    elif peek(line, '') == TOKENS.LESS_THAN:
        _ = consume(line)
        file_path = ''.join(takewhile(lambda token: token != TOKENS.GREATER_THAN, line))
        _ = error_if_not_value(line, TOKENS.GREATER_THAN)
        search_paths = chain(search_paths, include_dirs)
    else:
        raise ValueError('{l} Expected an IDENTIFIER, STRING or `<` got {g}'.format(
            l=loc(peek(line, EOFLocation)),  g=peek(line, '')
        ))
    return preprocess(
        tokenize(load(file_path, search_paths)), macros=macros, include_dirs=include_dirs
    )


def DEFINE(token_seq, macros, *_):
    line = get_line(token_seq)
    define_token = consume(line)
    name = consume(line)
    value = consume(line, default=IGNORE(''))
    if value == TOKENS.LEFT_PARENTHESIS and loc(name).column_number + len(name) == loc(value).column_number:
        arguments = []
        while peek(line, '') != TOKENS.RIGHT_PARENTHESIS:
            arguments.append(error_if_not_type(consume(line, EOFLocation), (IDENTIFIER, KEYWORD)))
            _ = peek(token_seq, '') == TOKENS.COMMA and consume(token_seq)
        _ = error_if_not_value(line, TOKENS.RIGHT_PARENTHESIS)
        macro = FunctionMacro(name, arguments, tuple(line))
    else:
        macro = ObjectMacro(name, tuple(chain((value,), line)))

    if name in macros:
        logger.warning('{l} Redefining macro {name}'.format(l=loc(name), name=name))
    macros[name] = macro
    yield IGNORE('', loc(define_token))


def UNDEF(token_seq, macros, *_):
    line = get_line(token_seq)
    _ = consume(line)
    macro_name = error_if_not_type(consume(line, EOFLocation), IDENTIFIER)
    error_if_not_empty(line)
    _ = macros.pop(macro_name, None)
    yield IGNORE('', loc(_))


def IF(token_seq, macros, preprocess, include_dirs):
    return if_block(token_seq, macros, preprocess, include_dirs)


def WARNING(token_seq, *_):
    t = peek(token_seq)
    logger.warning('{l} warning: {m}'.format(l=loc(t), m=' '.join(get_line(token_seq))))
    yield IGNORE('', loc(t))


def ERROR(token_seq, *_):
    t = peek(token_seq)
    raise ValueError('{l} error: {m}'.format(l=loc(t), m=' '.join(get_line(token_seq))))


def directive(token_seq, macros, preprocess, include_dirs):
    return directive.rules[peek(token_seq)](token_seq, macros, preprocess, include_dirs)
directive.rules = {   # We don't want to create this dictionary every time the function gets called.
    TOKENS.PINCLUDE: INCLUDE,
    TOKENS.PDEFINE: DEFINE,
    TOKENS.PUNDEF: UNDEF,

    TOKENS.PIF: IF,
    TOKENS.PIFDEF: IF,
    TOKENS.PIFNDEF: IF,

    TOKENS.PWARNING: WARNING,
    TOKENS.PERROR: ERROR,
}


def default(token_seq, macros, *_):
    token = consume(token_seq)
    return macros.get(token, d=token, all_tokens=token_seq)


def get_directives():
    directives = defaultdict(lambda: default)
    directives.update({rule: directive for rule in directive.rules})
    return directives