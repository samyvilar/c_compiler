__author__ = 'samyvilar'

from itertools import imap, repeat, chain, izip
from utils.rules import rules, set_rules
from utils.sequences import peek, consume, exhaust, takewhile
from front_end.loader.locations import loc, EOFLocation
from front_end.tokenizer.parser import get_line
from front_end.tokenizer.tokens import TOKENS, IDENTIFIER, KEYWORD
from front_end.parser import constant_expression
from front_end.parser.ast.expressions import exp
from front_end.tokenizer.tokens import INTEGER, IGNORE, digit
from utils.errors import error_if_not_empty, error_if_not_value, error_if_not_type


def nested_block(token_seq):
    for token in chain(get_line(token_seq), get_block(token_seq)):  # get the entire block ...
        yield token
    yield error_if_not_value(token_seq, TOKENS.PENDIF)


def non_nested_block(token_seq):
    yield consume(token_seq)


def get_block(token_seq, terminating_with={TOKENS.PENDIF}):
    return chain.from_iterable(
        imap(
            apply,
            imap(
                rules(get_block).__getitem__,
                takewhile(lambda token: token not in terminating_with, imap(peek, repeat(token_seq)))
            ),
            repeat((token_seq,))
        )
    )
set_rules(get_block, izip((TOKENS.PIF, TOKENS.PIFDEF, TOKENS.PIFNDEF), repeat(nested_block)), non_nested_block)


def expand(arguments, macros):
    for arg in imap(consume, repeat(arguments)):
        if isinstance(arg, (IDENTIFIER, KEYWORD)) or arg in macros:
            for token in macros.get(arg, INTEGER(digit(0), loc(arg)), arguments):
                yield token
        else:
            yield arg


def evaluate_expression(arguments, macros):
    return error_if_not_type(exp(constant_expression(expand(arguments, macros))), (long, int, float))


def _if_block(token_seq, macros):
    arguments = get_line(token_seq)
    return __calc_if(consume(arguments) and evaluate_expression(arguments, macros), token_seq, macros)


def _if_def_block(token_seq, macros):
    arguments = get_line(token_seq)
    argument = consume(arguments) and error_if_not_type(consume(arguments), (IDENTIFIER, KEYWORD))
    _ = error_if_not_empty(arguments)
    return __calc_if(argument in macros, token_seq, macros)


def _if_not_def_block(token_seq, macros):
    arguments = get_line(token_seq)
    argument = consume(arguments) and error_if_not_type(consume(arguments), (IDENTIFIER, KEYWORD))
    _ = error_if_not_empty(arguments)
    return __calc_if(argument not in macros, token_seq, macros)


def _else_block(token_seq, _):
    line = get_line(token_seq)
    _ = consume(line) and error_if_not_empty(line)
    return get_block(token_seq)


def pend_if(token_seq, _):
    yield IGNORE(location=loc(peek(token_seq)))


def invalid_token(token_seq, _):
    raise ValueError('{l} Expected either #elif, #else or #endif, got {g} for #if {at}'.format(
        l=loc(token_seq, EOFLocation), g=peek(token_seq, ''),
    ))


def exhaust_elif_block(token_seq):
    exhaust(get_block(token_seq, terminating_with={TOKENS.PELIF, TOKENS.PELSE, TOKENS.PENDIF}))


def exhaust_else_block(token_seq):
    exhaust(_else_block(token_seq, None))


def exhaust_remaining_blocks(token_seq):
    exhaust(
        imap(
            apply,
            imap(
                rules(exhaust_remaining_blocks).__getitem__,
                takewhile(TOKENS.PENDIF.__ne__, imap(peek, repeat(token_seq)))
            ),
            repeat((token_seq,))
        )
    )
set_rules(exhaust_remaining_blocks, ((TOKENS.PELIF, exhaust_elif_block), (TOKENS.PELSE, exhaust_else_block)))


def __calc_if(expr, token_seq, macros):
    tokens = get_block(token_seq, terminating_with={TOKENS.PELIF, TOKENS.PELSE, TOKENS.PENDIF})  # get a single block
    if not expr:  # if expression is false we have to exhaust ... and search for a true elif expression, else or endif
        _ = exhaust(tokens)
        tokens = rules(__calc_if)[peek(token_seq)](token_seq, macros)

    for t in imap(consume, repeat(tokens)):  # emit tokens which will be pre-processed ...
        yield t

    exhaust_remaining_blocks(token_seq)
set_rules(__calc_if, ((TOKENS.PENDIF, pend_if), (TOKENS.PELIF, _if_block), (TOKENS.PELSE, _else_block)))


def if_block(token_seq, macros):
    for token in macros['__ preprocess __'](rules(if_block)[peek(token_seq)](token_seq, macros), macros):
        yield token
    _ = error_if_not_value(token_seq, TOKENS.PENDIF)
set_rules(if_block, ((TOKENS.PIF, _if_block), (TOKENS.PIFDEF, _if_def_block), (TOKENS.PIFNDEF, _if_not_def_block)))