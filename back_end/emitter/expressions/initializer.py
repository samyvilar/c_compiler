__author__ = 'samyvilar'

from itertools import chain, imap, repeat, izip

from utils.rules import set_rules, rules
from utils.sequences import reverse

from front_end.loader.locations import loc
from front_end.parser.types import ArrayType, UnionType, StructType, c_type
from front_end.parser.ast.expressions import Initializer
from front_end.parser.expressions.initializer import scalar_types

from back_end.emitter.c_types import size

from back_end.virtual_machine.instructions.architecture import allocate


def numeric_initializer(expr, symbol_table):
    return symbol_table['__ expression __'](expr[0], symbol_table)


def union_initializer(expr, symbol_table):
    return chain(
        allocate(size(c_type(expr)) - size(c_type(expr[0])), loc(expr)), numeric_initializer(expr, symbol_table)
    )


def initializer_exprs_flatten(expr):
    for e in expr.itervalues():
        if isinstance(e, Initializer):
            for v in initializer_exprs_flatten(e):
                yield v
        else:
            yield e


def struct_initializer(expr, symbol_table):
    return chain.from_iterable(
        imap(symbol_table['__ expression __'], reverse(initializer_exprs_flatten(expr)), repeat(symbol_table))
    )


def array_initializer(expr, symbol_table):
    return struct_initializer(expr, symbol_table)
    # def _instrs(expr, symbol_table):  # TODO: deal with ranged designated exprs which should only be evaluated once
    #     expression = symbol_table['__ expression __']
    #     for count, sub_exp in count_identical_expressions(flatten_initializer_expressions(expr)):
    #         instrs = expression(sub_exp, symbol_table)
    #         if count > 1:
    #             instrs = chain(instrs, dup(size(c_type(sub_exp)), loc(sub_exp)))
    #         yield instrs
    #
    # return chain.from_iterable(reversed(tuple(_instrs(expr, symbol_table))))


# def flatten_initializer_expressions(expr):
#     for value in expr.itervalues():
#         yield value
#
#
# def count_identical_expressions(exprs):
#     count, previous_expr = 0, None
#     for current_exp in imap(peek, repeat(exprs)):
#         while current_exp is peek_or_terminal(exprs):
#             current_exp = consume(exprs)
#             count += 1
#         yield count, current_exp


def _initializer_expression(expr, symbol_table):
    return rules(_initializer_expression)[type(c_type(expr))](expr, symbol_table)

set_rules(
    _initializer_expression,
    chain(
        izip(scalar_types, repeat(numeric_initializer)),
        (
            (StructType, struct_initializer),
            (UnionType, union_initializer),
            (ArrayType, array_initializer)
        ),
    )
)


def initializer_expression(expr, symbol_table):
    return _initializer_expression(expr, symbol_table)
set_rules(initializer_expression, {Initializer})

