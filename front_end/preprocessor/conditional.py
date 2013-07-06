__author__ = 'samyvilar'

from sequences import peek, consume, takewhile
from front_end.loader.locations import loc
from front_end.tokenizer.parser import get_line
from front_end.tokenizer.tokens import TOKENS, IDENTIFIER
from front_end.parser.expressions.expression import constant_expression
from front_end.tokenizer.tokens import INTEGER, IGNORE
from front_end.errors import error_if_not_empty, error_if_not_value


def exhaust(token_seq):
    for token in token_seq:
        if token in {TOKENS.PIF, TOKENS.PIFDEF, TOKENS.PIFNDEF}:
            exhaust(takewhile(lambda token: token != TOKENS.PENDIF, token_seq))


def expand(arguments, macros):
    args = []
    for arg in arguments:
        if isinstance(arg, IDENTIFIER):
            args.extend(macros.get(arg, [INTEGER('0', loc(arg))], arguments))
        else:
            args.append(arg)
    return args


def evaluate_expression(arguments, macros):
    arguments = expand(arguments, macros)
    exp = constant_expression(iter(arguments), {})
    return exp.exp


def _if_block(token_seq, macros, preprocess):
    arguments = get_line(token_seq)
    _ = consume(arguments)
    if_body = takewhile(lambda token: token not in {TOKENS.PELIF, TOKENS.PELSE, TOKENS.PENDIF}, token_seq)

    if evaluate_expression(arguments, macros):
        tokens = preprocess(if_body, macros=macros)
    else:
        exhaust(if_body)
        token = peek(token_seq, default='')
        if token == TOKENS.PENDIF:
            tokens = [IGNORE(peek(token_seq), loc(token))]
        elif token == TOKENS.PELIF:
            tokens = _if_block(token_seq, macros, preprocess)
        elif token == TOKENS.ELSE:
            tokens = _else_block(token_seq, macros, preprocess)
        else:
            raise ValueError('{l} Expected either #elif, #else or #endif'.format(l=token and loc(token)))

    for t in tokens:
        yield t

    while peek(token_seq, default='') != TOKENS.PENDIF:
        token = consume(token_seq)
        if token == TOKENS.PELIF:
            exhaust(takewhile(lambda token: token not in {TOKENS.PELIF, TOKENS.PELSE, TOKENS.PENDIF}, token_seq))
        elif token == TOKENS.PELSE:
            exhaust(takewhile(lambda token: token not in {TOKENS.PELIF, TOKENS.PELSE, TOKENS.PENDIF}, token_seq))
            error_if_not_value(token_seq, TOKENS.PENDIF)
        else:
            raise ValueError('{l} Expected either #elif, #else, #endif got {got}'.format(l=loc(token), got=token))
    token = error_if_not_value(token_seq, TOKENS.PENDIF)
    yield IGNORE(token, loc(token))


def _else_block(token_seq, macros, preprocess):
    line = get_line(token_seq)
    _ = consume(token_seq)
    error_if_not_empty(line)
    else_body = takewhile(lambda token: token != TOKENS.PENDIF, token_seq)
    return preprocess(else_body, macros=macros)



def _if_def_block(token_seq, macros, preprocess):
    pass


def if_not_def_block(token_seq, macros, preprocess):
    pass


def if_block(token_seq, macros, preprocess):
    return if_block.rules[peek(token_seq)](token_seq, macros, preprocess)
if_block.rules = {
    TOKENS.PIF: _if_block,
    TOKENS.PIFDEF: _if_def_block,
    TOKENS.PIFNDEF: if_not_def_block,
}