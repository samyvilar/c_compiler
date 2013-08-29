__author__ = 'samyvilar'

from itertools import chain, izip, repeat

from front_end.loader.locations import loc

from front_end.parser.ast.declarations import name
from front_end.parser.ast.expressions import ConstantExpression, CastExpression, IdentifierExpression
from front_end.parser.ast.expressions import BinaryExpression, AssignmentExpression, CompoundAssignmentExpression
from front_end.parser.ast.expressions import EmptyExpression
from front_end.parser.types import c_type, FunctionType, ArrayType

from back_end.emitter.expressions.cast import cast_expression
from back_end.emitter.expressions.constant import constant_expression
from back_end.emitter.expressions.binary import binary_expression
from back_end.emitter.expressions.unary import unary_expression
from back_end.emitter.expressions.postfix import postfix_expression
from back_end.emitter.expressions.ternary import ternary_expression

from back_end.emitter.c_types import size

from back_end.virtual_machine.instructions.architecture import Load


def identifier_expression(expr, symbol_table, expression_func):
    # Defaults to Load, assignment expression will update it to set.
    dec = symbol_table[name(expr)]
    if isinstance(c_type(dec), (FunctionType, ArrayType)):  # Function/Array Types are nothing more than addresses.
        return dec.load_address(loc(expr))
    return chain(dec.load_address(loc(expr)), (Load(loc(expr), size(c_type(expr))),),)


# Entry point to all expression or expression statements
def expression(expr, symbol_table=None, expression_func=None):
    return expression.rules[type(expr)](expr, symbol_table or {}, expression_func or expression)
expression.rules = {
    EmptyExpression: lambda expr, *_: (),
    ConstantExpression: constant_expression,
    CastExpression: cast_expression,
    IdentifierExpression: identifier_expression,

    BinaryExpression: binary_expression,
    AssignmentExpression: binary_expression,
    CompoundAssignmentExpression: binary_expression,
}
expression.rules.update(chain(
    izip(unary_expression.rules, repeat(unary_expression)),
    izip(postfix_expression.rules, repeat(postfix_expression)),
    izip(ternary_expression.rules, repeat(ternary_expression))
))