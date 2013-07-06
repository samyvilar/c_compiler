__author__ = 'samyvilar'

from sequences import peek, consume
from collections import defaultdict
from itertools import chain

from front_end.preprocessor import logger
from front_end.preprocessor.conditional import if_block

from front_end.loader.load import load
from front_end.tokenizer.tokenize import tokenize
from front_end.tokenizer.parser import get_line
from front_end.tokenizer.tokens import TOKENS, STRING, IDENTIFIER, IGNORE, TOKEN

from front_end.loader.locations import loc
from front_end.preprocessor.macros import ObjectMacro, FunctionMacro

from front_end.errors import error_if_not_type, error_if_not_value, error_if_not_empty


def INCLUDE(token_seq, macros, preprocess):
    line = get_line(token_seq)
    _ = consume(line)
    token = consume(line)
    if isinstance(token, STRING):
        file_path = token
    else:
        raise ValueError('{l} Expected an IDENTIFIER or STRING for directive {d} got {}'.format(
            l=loc(token), d=type(token), g=token
        ))
    return preprocess(tokenize(load(file_path)), macros=macros)


def DEFINE(token_seq, macros, _):
    line = get_line(token_seq)
    define_token = consume(line)
    name = consume(line)
    value = consume(line, default=TOKEN(''))
    if value == TOKENS.LEFT_PARENTHESIS and loc(name).column_number + 1 == loc(value).column_number:
        arguments = []
        while peek(line, default='') != TOKENS.RIGHT_PARENTHESIS:
            arguments.append(error_if_not_type(line, IDENTIFIER))
            _ = peek(token_seq, default='') == TOKENS.COMMA and consume(token_seq)
        _ = error_if_not_value(line, TOKENS.RIGHT_PARENTHESIS)
        macro = FunctionMacro(name, arguments, list(line))
    else:
        macro = ObjectMacro(name, list(chain([value], line)))

    if name in macros:
        logger.warning('{l} Redefining macro {name}'.format(l=loc(name), name=name))
    macros[name] = macro
    yield IGNORE(define_token, loc(define_token))


def UNDEF(token_seq, macros, _):
    line = get_line(token_seq)
    undef_token = consume(line)
    macro_name = error_if_not_type(line, IDENTIFIER)
    error_if_not_empty(line)
    _ = macros.pop(macro_name, None)
    yield IGNORE(undef_token)


def IF(token_seq, macros, preprocess):
    return if_block(token_seq, macros, preprocess)


def directive(token_seq, macros, preprocess):
    return directive.rules[peek(token_seq)](token_seq, macros, preprocess)
directive.rules = {   # We don't want to create this dictionary every time the function gets called.
    TOKENS.PINCLUDE: INCLUDE,
    TOKENS.PDEFINE: DEFINE,
    TOKENS.PUNDEF: UNDEF,

    TOKENS.PIF: IF,
    TOKENS.PIFDEF: IF,
    TOKENS.PIFNDEF: IF
}


def default(token_seq, macros, _):
    token = consume(token_seq)
    if token.startswith('#'):
        raise ValueError('{l} Preprocessor directive {d} doesnt exist.'.format(l=loc(token), d=token))
    return macros.get(token, d=token, all_tokens=token_seq)


def get_directives():
    directives = defaultdict(lambda: default)
    directives.update({rule: directive for rule in directive.rules})
    return directives