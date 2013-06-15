__author__ = 'samyvilar'

import os
from collections import defaultdict

from front_end.preprocessor import logger
from front_end.preprocessor.conditional import if_block
from front_end.tokenizer.tokenize import Tokenize, line_tokens
from front_end.tokenizer.tokens import TOKENS, STRING, IDENTIFIER
from front_end.loader.load import Load
from front_end.loader.locations import loc
from front_end.preprocessor.macros import ObjectMacro, FunctionMacro

from front_end.errors import error_if_not_type, error_if_not_value, error_if_not_empty


def INCLUDE(all_tokens, macros, _, tokens, token):
    if isinstance(tokens[0], IDENTIFIER) and tokens[0] in macros:
        file_path = macros[tokens.pop(0), tokens]
    else:
        file_path = error_if_not_type(tokens, STRING)
    error_if_not_empty(tokens)

    if not os.path.isfile(file_path):
        raise ValueError('{l} Could not include file {f}.'.format(f=file_path, l=loc(token)))
    new_tokens = Tokenize(Load(file_path))
    new_tokens.extend(all_tokens)
    return new_tokens


def DEFINE(all_tokens, macros, *args):
    tokens = args[1]
    name = error_if_not_type(tokens, IDENTIFIER)

    if tokens \
        and tokens[0] == TOKENS.LEFT_PARENTHESIS \
            and loc(name).column_number + 1 == loc(tokens[0]).column_number:
        _ = tokens.pop(0)  # pop parenthesis.
        func_macro_arguments = Tokenize()
        while tokens and tokens[0] != TOKENS.RIGHT_PARENTHESIS:
            func_macro_arguments.append(error_if_not_type(tokens, IDENTIFIER))
            _ = tokens and tokens[0] == TOKENS.COMMA and tokens.pop(0)
        _ = error_if_not_value(tokens, TOKENS.RIGHT_PARENTHESIS)  # pop right parenthesis.
        macro = FunctionMacro(name, func_macro_arguments, tokens)
    else:
        macro = ObjectMacro(name, tokens)

    if name in macros:
        logger.warning('Redefining macro {name}'.format(name=name), extra={'location': loc(name)})
    macros[name] = macro
    return all_tokens


def UNDEF(all_tokens, macros, *args):
    tokens = args[1]
    macro_name = error_if_not_type(tokens, IDENTIFIER)
    error_if_not_empty(tokens)
    _ = macros.pop(macro_name, None)
    return all_tokens


def IF(all_tokens, macros, new_tokens, line, current_token):
    body = if_block(all_tokens, macros, new_tokens, line, current_token).evaluate(macros)
    body.extend(all_tokens)
    return body


def directive(all_tokens, macros, new_tokens):
    line = line_tokens(all_tokens)
    return directive.rules[line[0]](all_tokens, macros, new_tokens, line, line.pop(0))
directive.rules = {   # We don't want to create this dictionary every time the function gets called.
    TOKENS.PINCLUDE: INCLUDE,
    TOKENS.PDEFINE: DEFINE,
    TOKENS.PUNDEF: UNDEF,

    TOKENS.PIF: IF,
    TOKENS.PIFDEF: IF,
    TOKENS.PIFNDEF: IF
}


def get_directives():
    return get_directives.directives
get_directives.directives = defaultdict(lambda: default)
get_directives.directives.update({
    TOKENS.PINCLUDE: directive,
    TOKENS.PDEFINE: directive,
    TOKENS.PUNDEF: directive,
    TOKENS.PIF: directive,
    TOKENS.PIFDEF: directive,
    TOKENS.PIFNDEF: directive,
})


def default(all_tokens, macros, new_tokens):
    if all_tokens[0].startswith('#'):
        raise ValueError('{l} Preprocessor directive {d} doesnt exist.'.format(
            l=loc(all_tokens[0]), d=all_tokens[0]
        ))
    new_tokens.extend(macros.get(all_tokens[0], (all_tokens.pop(0),), all_tokens))
    return all_tokens
