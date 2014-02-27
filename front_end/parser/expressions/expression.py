__author__ = 'samyvilar'

from itertools import repeat, takewhile, starmap, chain

from utils.sequences import peek, consume, peek_or_terminal
from front_end.loader.locations import loc
from front_end.tokenizer.tokens import TOKENS

from front_end.parser.types import c_type

from front_end.parser.ast.expressions import CommaExpression

from loggers import logging


logger = logging.getLogger('parser')


def expression(tokens, symbol_table):  # assignment_expression (',' assignment_expression)*
    assignment_expression = symbol_table['__ assignment_expression __']
    expr = assignment_expression(tokens, symbol_table)

    if peek_or_terminal(tokens) == TOKENS.COMMA:
        exprs = tuple(chain(
            (expr,),
            starmap(
                assignment_expression,
                takewhile(
                    lambda a: peek_or_terminal(a[0]) == TOKENS.COMMA and consume(a[0]),
                    repeat((tokens, symbol_table))
                )
            )
        ))
        expr = CommaExpression(exprs, c_type(exprs[-1]), loc(exprs[-1]))

    return expr