__author__ = 'samyvilar'

from sequences import peek, consume
from front_end.loader.locations import loc
from front_end.tokenizer.parser import get_line
from front_end.tokenizer.tokens import TOKENS, IDENTIFIER, KEYWORD
from front_end.parser.expressions.expression import constant_expression
from front_end.parser.ast.expressions import exp
from front_end.tokenizer.tokens import INTEGER, IGNORE
from front_end.errors import error_if_not_empty, error_if_not_value


def exhaust(
        token_seq,
        takewhile=lambda token_seq:
        peek(token_seq, default=TOKENS.PENDIF) not in {TOKENS.PELIF, TOKENS.PELSE, TOKENS.PENDIF}
):
    while takewhile(token_seq):
        if consume(token_seq) in {TOKENS.PIF, TOKENS.PIFDEF, TOKENS.PIFNDEF}:   # nested if blocks...
            exhaust(token_seq, takewhile=lambda token_seq: peek(token_seq, default=TOKENS.PENDIF) != TOKENS.PENDIF)
            _ = error_if_not_value(token_seq, TOKENS.PENDIF)


def expand(arguments, macros):
    args = []
    for arg in arguments:
        if isinstance(arg, (IDENTIFIER, KEYWORD)):
            args.extend(macros.get(arg, d=INTEGER('0', loc(arg)), all_tokens=arguments))
        else:
            args.append(arg)
    return args


def evaluate_expression(arguments, macros):
    return exp(constant_expression(iter(expand(arguments, macros)), {}))


def __calc_if(if_token, token_seq, expr, preprocess, macros, include_dirs):
    if expr():
        tokens = preprocess(
            token_seq,
            macros=macros,
            include_dirs=include_dirs,
            takewhile=lambda token_seq:
            peek(token_seq, default=TOKENS.PENDIF) not in {TOKENS.PELIF, TOKENS.PELSE, TOKENS.PENDIF}
        )
    else:
        exhaust(token_seq)
        token = peek(token_seq, default='')
        if token == TOKENS.PENDIF:
            tokens = (IGNORE(peek(token_seq), loc(token)),)
        elif token == TOKENS.PELIF:
            tokens = _if_block(token_seq, macros, preprocess, include_dirs)
        elif token == TOKENS.PELSE:
            tokens = _else_block(token_seq, macros, preprocess, include_dirs)
        else:
            raise ValueError('{l} Expected either #elif, #else or #endif, got {g} for #if {at}'.format(
                l=loc(token), g=token, at=loc(if_token),
            ))

    for t in tokens:
        yield t

    while peek(token_seq, default=TOKENS.PENDIF) != TOKENS.PENDIF:
        token = consume(token_seq)
        if token == TOKENS.PELIF:
            exhaust(
                token_seq,
                takewhile=lambda token_seq:
                peek(token_seq, default=TOKENS.PENDIF) not in {TOKENS.PELIF, TOKENS.PELSE, TOKENS.PENDIF}
            )
        elif token == TOKENS.PELSE:
            exhaust(token_seq, takewhile=lambda token_seq: peek(token_seq, default=TOKENS.PENDIF) != TOKENS.PENDIF)
            break
        else:
            raise ValueError('{l} Expected either #elif, #else or #endif, got {g} for #if {at}'.format(
                l=loc(token), g=token, at=loc(if_token),
            ))
    yield IGNORE('')


def _if_block(token_seq, macros, preprocess, include_dirs):
    arguments = get_line(token_seq)
    return __calc_if(
        consume(arguments),
        token_seq,
        lambda a=arguments, m=macros: evaluate_expression(a, m),
        preprocess,
        macros,
        include_dirs
    )


def _else_block(token_seq, macros, preprocess, include_dirs):
    line = get_line(token_seq)
    _ = consume(token_seq)
    error_if_not_empty(line)
    return preprocess(
        token_seq,
        macros=macros,
        include_dirs=include_dirs,
        takewhile=lambda token_seq: peek(token_seq, default=TOKENS.PENDIF) != TOKENS.PENDIF
    )


def _if_def_block(token_seq, macros, preprocess, include_dirs):
    arguments = get_line(token_seq)
    if_token = consume(token_seq)
    arguments = tuple(arguments)
    if len(arguments) != 1 or not isinstance(arguments[0], (IDENTIFIER, KEYWORD)):
        raise ValueError('{l} expected a single IDENTIFIER token got {g}'.format(l=loc(_), g=arguments or ''))
    return __calc_if(
        if_token,
        token_seq, lambda ident=arguments[0], m=macros: ident in m,
        preprocess,
        macros,
        include_dirs,
    )


def if_not_def_block(token_seq, macros, preprocess, include_dirs):
    arguments = get_line(token_seq)
    if_token = consume(token_seq)
    arguments = tuple(arguments)
    if len(arguments) != 1 or not isinstance(arguments[0], (IDENTIFIER, KEYWORD)):
        raise ValueError('{l} expected a single IDENTIFIER token got {g}'.format(l=loc(_), g=arguments or ''))
    return __calc_if(
        if_token,
        token_seq, lambda ident=arguments[0], m=macros: ident not in m,
        preprocess,
        macros,
        include_dirs
    )


def if_block(token_seq, macros, preprocess, include_dirs):
    for token in if_block.rules[peek(token_seq)](token_seq, macros, preprocess, include_dirs):
        yield token
    _ = error_if_not_value(token_seq, TOKENS.PENDIF)
if_block.rules = {
    TOKENS.PIF: _if_block,
    TOKENS.PIFDEF: _if_def_block,
    TOKENS.PIFNDEF: if_not_def_block,
}