__author__ = 'samyvilar'

import os
from itertools import chain, izip, repeat

from utils.sequences import peek, consume, takewhile, consume_all, peek_or_terminal
from utils.rules import rules, set_rules, get_rule, identity

from front_end.loader.locations import loc, EOFLocation, column_number

from front_end.preprocessor import logger
from front_end.preprocessor.conditional import if_block
from front_end.loader.load import load
from front_end.tokenizer.tokenize import tokenize
from front_end.tokenizer.parser import get_line
from front_end.tokenizer.tokens import TOKENS, STRING, IDENTIFIER, IGNORE, KEYWORD, filter_out_empty_tokens, empty_token

from front_end.preprocessor.macros import ObjectMacro, FunctionMacro
from front_end.preprocessor.macros import FunctionMacroArgument, FunctionMacroVariadicArgument

from utils.symbol_table import SymbolTable, push, pop

from utils.errors import error_if_not_type, error_if_not_value, error_if_not_empty, raise_error


def pop_macros(macros):
    yield (pop(macros) or 1) and empty_token


def string_file_path(token_seq, _):
    return consume(token_seq)


def identifier_file_path(token_seq, macros):
    return macros.get(peek(token_seq), consume(token_seq), token_seq)


def standard_lib_file_path(token_seq, _):
    file_path = consume(token_seq) and ''.join(takewhile(TOKENS.GREATER_THAN.__ne__, token_seq))
    _ = error_if_not_value(token_seq, TOKENS.GREATER_THAN)
    return file_path


def INCLUDE(token_seq, macros):
    line = get_line(token_seq)
    file_path = consume(line) and get_rule(INCLUDE, peek_or_terminal(line), hash_funcs=(type, identity))(line, macros)
    search_paths = (os.getcwd(),)
    _ = error_if_not_empty(line)
    return chain(
        macros['__ preprocess __'](
            tokenize(load(file_path, chain(macros['__ include_dirs __'], search_paths))),
            macros
        ),
    )
set_rules(
    INCLUDE,
    (
        (STRING, string_file_path),
        izip((IDENTIFIER, KEYWORD), repeat(identifier_file_path)),
        (TOKENS.LESS_THAN, standard_lib_file_path)
    )
)


def _func_macro_arguments(line):
    symbol_table = SymbolTable()
    while peek(line, TOKENS.RIGHT_PARENTHESIS) != TOKENS.RIGHT_PARENTHESIS:
        if peek(line) == TOKENS.ELLIPSIS:
            arg = FunctionMacroVariadicArgument(IDENTIFIER('__VA_ARGS__', loc(consume(line))))
        else:
            arg = FunctionMacroArgument(error_if_not_type(consume(line, EOFLocation), (IDENTIFIER, KEYWORD)))
            if peek_or_terminal(line) == TOKENS.ELLIPSIS:
                arg = FunctionMacroVariadicArgument(IDENTIFIER(arg, loc(consume(line))))
        symbol_table[arg] = arg     # check for duplicate argument name
        yield arg       # if ok add to the rest ...
        if isinstance(arg, FunctionMacroVariadicArgument):  # if variadic argument break ...
            break
        # consume expected comma if we don't see a right parenthesis ...
        _ = peek(line, TOKENS.RIGHT_PARENTHESIS) != TOKENS.RIGHT_PARENTHESIS \
            and error_if_not_value(line, TOKENS.COMMA, loc(arg))


def _func_macro_definition(name, line):
    arguments = tuple(_func_macro_arguments(line))  # defining function macro
    _ = error_if_not_value(line, TOKENS.RIGHT_PARENTHESIS, loc(name))
    return FunctionMacro(name, arguments, tuple(filter_out_empty_tokens(line)))


def DEFINE(token_seq, macros):
    line = get_line(token_seq)
    define_token = consume(line)
    name = consume(line)
    value = consume(line, default=IGNORE())
    if value == TOKENS.LEFT_PARENTHESIS and column_number(name) + len(name) == column_number(value):
        macro = _func_macro_definition(name, line)
    else:  # object macro
        macro = ObjectMacro(name, tuple(filter_out_empty_tokens(chain((value,), line))))

    _ = name in macros and macros.pop(name) and logger.warning('{0} Redefining macro {1}'.format(loc(name), name))

    macros[name] = macro
    yield IGNORE(location=loc(define_token))


def UNDEF(token_seq, macros):
    line = get_line(token_seq)
    macro_name = consume(line) and error_if_not_type(consume(line, EOFLocation), (IDENTIFIER, KEYWORD))
    _ = macro_name in macros and macros.pop(macro_name)
    _ = error_if_not_empty(line)
    yield IGNORE(location=loc(macro_name))


def WARNING(token_seq, *_):
    t = peek(token_seq)
    logger.warning('{l} warning: {m}'.format(l=loc(t), m=' '.join(get_line(token_seq))))
    yield IGNORE(location=loc(t))


def ERROR(token_seq, *_):
    t = peek(token_seq)
    raise_error('{l} error: {m}'.format(l=loc(t), m=' '.join(get_line(token_seq))))


def expand_token(token_seq, macros):
    return macros.get(peek(token_seq), consume(token_seq), token_seq)


def directive(token_seq, macros):
    return rules(directive)[peek(token_seq)](token_seq, macros)
set_rules(
    directive,
    (
        (TOKENS.PINCLUDE, INCLUDE), (TOKENS.PDEFINE, DEFINE), (TOKENS.PUNDEF, UNDEF),
        (TOKENS.PIF, if_block), (TOKENS.PIFDEF, if_block), (TOKENS.PIFNDEF, if_block),
        (TOKENS.PWARNING, WARNING), (TOKENS.PERROR, ERROR),
    ),
    expand_token
)


def get_directives():
    return rules(directive)
