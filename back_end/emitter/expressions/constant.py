__author__ = 'samyvilar'

from front_end.loader.locations import loc
from back_end.emitter.object_file import String
from back_end.emitter.types import binaries, size

from front_end.parser.ast.declarations import Static
from front_end.parser.ast.expressions import exp

from front_end.parser.types import CharType, ShortType, IntegerType, LongType, FloatType, DoubleType, PointerType
from front_end.parser.types import StringType, c_type

from back_end.virtual_machine.instructions.architecture import Push, Integer, Double, Address


def const_string_expr(expr):
    symbol = String(repr(expr), binaries(expr), size(c_type(expr)), Static(loc(expr)), loc(expr))
    yield symbol
    yield Push(loc(expr), Address(symbol, loc(expr)))


def const_integral_expr(expr):
    yield Push(loc(expr), Integer(exp(expr), loc(expr)))


def const_float_expr(expr):
    yield Push(loc(expr), Double(exp(expr), loc(expr)))


def constant_expression(expr, *_):
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
