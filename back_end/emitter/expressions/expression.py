__author__ = 'samyvilar'

from itertools import chain, izip, repeat, imap

from utils.rules import rules, set_rules

from front_end.loader.locations import loc

from front_end.parser.ast.declarations import name
from front_end.parser.ast.expressions import ConstantExpression, CastExpression, IdentifierExpression, exp
from front_end.parser.ast.expressions import BinaryExpression, AssignmentExpression, CompoundAssignmentExpression
from front_end.parser.ast.expressions import EmptyExpression, CommaExpression
from front_end.parser.types import c_type, FunctionType, ArrayType, VoidType

from back_end.emitter.expressions.cast import cast_expression
from back_end.emitter.expressions.constant import constant_expression
from back_end.emitter.expressions.binary import binary_expression
from back_end.emitter.expressions.unary import unary_expression
from back_end.emitter.expressions.postfix import postfix_expression
from back_end.emitter.expressions.ternary import ternary_expression
from back_end.emitter.expressions.initializer import initializer_expression

from back_end.emitter.c_types import size_arrays_as_pointers, size

from back_end.virtual_machine.instructions.architecture import load, allocate


def identifier_expression(expr, symbol_table):
    # Defaults to Load, assignment expression will update it to set.
    dec = symbol_table[name(expr)]
    if isinstance(c_type(dec), (FunctionType, ArrayType)):  # Function/Array Types are nothing more than addresses.
        return dec.load_address(loc(expr))
    return load(dec.load_address(loc(expr)), size_arrays_as_pointers(c_type(expr)), loc(expr))


def comma_expression(expr, symbol_table):
    expression = symbol_table['__ expression __']
    return chain(
        chain.from_iterable(
            chain(
                expression(e, symbol_table),
                allocate(-size_arrays_as_pointers(c_type(e), overrides={VoidType: 0}), loc(e))
            ) for e in exp(expr)[:-1]
        ),
        expression(exp(expr)[-1], symbol_table)
    )


# Entry point to all expression or expression statements
def expression(expr, symbol_table):
    return rules(expression)[type(expr)](expr, symbol_table)
expression_funcs = unary_expression, postfix_expression, ternary_expression, initializer_expression
set_rules(
    expression,
    chain(
        (
            (EmptyExpression, lambda expr, *_: allocate(size(c_type(expr), overrides={VoidType: 0}), loc(expr))),
            (ConstantExpression, constant_expression),
            (CastExpression, cast_expression),
            (IdentifierExpression, identifier_expression),
            (CommaExpression, comma_expression),

            (BinaryExpression, binary_expression),
            (AssignmentExpression, binary_expression),
            (CompoundAssignmentExpression, binary_expression),
        ),
        chain.from_iterable(imap(izip, imap(rules, expression_funcs), imap(repeat, expression_funcs)))
    )
)
