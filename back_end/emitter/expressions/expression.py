__author__ = 'samyvilar'

from itertools import chain, izip, repeat

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

from back_end.emitter.c_types import size

from back_end.virtual_machine.instructions.architecture import load_instr, allocate, Address


def identifier_expression(expr, symbol_table, expression_func):
    # Defaults to Load, assignment expression will update it to set.
    dec = symbol_table[name(expr)]
    if isinstance(c_type(dec), (FunctionType, ArrayType)):  # Function/Array Types are nothing more than addresses.
        return dec.load_address(loc(expr))
    return load_instr(dec.load_address(loc(expr)), size(c_type(expr)), loc(expr))


def comma_expression(expr, symbol_table, expression_func):
    return chain(
        chain.from_iterable(
            chain(
                expression_func(e, symbol_table, expression_func),
                not isinstance(c_type(e), VoidType) and allocate(-1 * size(c_type(e)), loc(e)) or ()
            )
            for e in exp(expr)[:-1]
        ),
        expression_func(exp(expr)[-1], symbol_table, expression_func)
    )


# Entry point to all expression or expression statements
def expression(expr, symbol_table=None, expression_func=None):
    return expression.rules[type(expr)](expr, symbol_table or {}, expression_func or expression)
expression.rules = {
    EmptyExpression: lambda expr, *_: (),
    ConstantExpression: constant_expression,
    CastExpression: cast_expression,
    IdentifierExpression: identifier_expression,
    CommaExpression: comma_expression,

    BinaryExpression: binary_expression,
    AssignmentExpression: binary_expression,
    CompoundAssignmentExpression: binary_expression,
}
expression.rules.update(chain(
    izip(unary_expression.rules, repeat(unary_expression)),
    izip(postfix_expression.rules, repeat(postfix_expression)),
    izip(ternary_expression.rules, repeat(ternary_expression))
))