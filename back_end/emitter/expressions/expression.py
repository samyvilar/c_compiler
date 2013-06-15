__author__ = 'samyvilar'

from front_end.loader.locations import loc

from front_end.parser.symbol_table import SymbolTable

from front_end.parser.ast.declarations import Static, name
from front_end.parser.ast.expressions import exp, ConstantExpression, CastExpression, IdentifierExpression
from front_end.parser.ast.expressions import BinaryExpression, AssignmentExpression, CompoundAssignmentExpression
from front_end.parser.ast.expressions import EmptyExpression

from front_end.parser.types import CharType, ShortType, IntegerType, LongType, FloatType, DoubleType, PointerType
from front_end.parser.types import StringType, c_type

from back_end.emitter.instructions.stack_state import Stack

from back_end.emitter.expressions.cast import cast_expression

from back_end.virtual_machine.instructions.architecture import Push, Integer, Double, Address, Allocate
from back_end.emitter.expressions.binary import binary_expression
from back_end.emitter.expressions.unary import unary_expression
from back_end.emitter.expressions.postfix import postfix_expression
from back_end.emitter.instructions.data import load_instructions

from back_end.emitter.object_file import Data
from back_end.emitter.types import binaries, size


def const_string_expr(expr):
    symbol = Data(
        repr(exp(expr)) + '.' + str(loc(expr).line_number),
        binaries(expr),
        size(c_type(expr)),
        Static(loc(expr)),
        loc(expr)
    )
    return [symbol, Push(loc(expr), Address(symbol, loc(expr)))]


def const_integral_expr(expr):
    return [Push(loc(expr), Integer(exp(expr), loc(expr)))]


def const_float_expr(expr):
    return [Push(loc(expr), Double(exp(expr), loc(expr)))]


def constant_expression(expr, symbol_table, stack, expression_func, jump_props):
    return constant_expression.rules[type(c_type(expr))](expr)
constant_expression.rules = {
    CharType: const_integral_expr,
    ShortType: const_integral_expr,
    IntegerType: const_integral_expr,
    LongType: const_integral_expr,
    PointerType: const_integral_expr,

    FloatType: const_float_expr,
    DoubleType: const_float_expr,
    StringType: const_string_expr
}


def identifier_expression(expr, symbol_table, stack, expression_func, jump_props):
    # Defaults to Load, assignment expression will update it to set.
    return load_instructions(symbol_table[name(expr)], loc(expr))


# Entry point to all expression or expression statements
def expression(expr, symbol_table=None, stack=None, expression_func=None, jump_props=()):
    instrs = expression.rules[type(expr)](
        expr,
        symbol_table or SymbolTable(),
        stack or Stack(),
        expression_func or expression,
        jump_props
    )
    # Every other recursive call to expression uses expression_func as expression
    # Entry point even from statement will set expression_func to false/None.
    if not expression_func:  # Append postfix instrs
        instrs.extend(postfix_expression.late_instrs)
        postfix_expression.late_instrs[:] = []

    return instrs
expression.rules = {
    EmptyExpression: lambda expr, *_: [Allocate(loc(expr), size(c_type(expr)))],
    ConstantExpression: constant_expression,
    CastExpression: cast_expression,
    IdentifierExpression: identifier_expression,

    BinaryExpression: binary_expression,
    AssignmentExpression: binary_expression,
    CompoundAssignmentExpression: binary_expression,
}
expression.rules.update({rule: unary_expression for rule in unary_expression.rules})
expression.rules.update({rule: postfix_expression for rule in postfix_expression.rules})