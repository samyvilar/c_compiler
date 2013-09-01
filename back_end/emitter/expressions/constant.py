__author__ = 'samyvilar'

from itertools import chain

from sequences import reverse, flatten

from front_end.loader.locations import loc
from back_end.emitter.c_types import binaries, size


from front_end.parser.ast.expressions import exp

from front_end.parser.types import CharType, ShortType, IntegerType, LongType, FloatType, DoubleType, PointerType
from front_end.parser.types import StringType, c_type, StructType, ArrayType

from back_end.virtual_machine.instructions.architecture import Push, Integer, Double, Address, Pass, Add, RelativeJump


def const_string_expr(expr):
    start_of_data, end_of_data = Pass(loc(expr)), Pass(loc(expr))
    return chain(
        (RelativeJump(loc(expr), Address(end_of_data, loc(expr))), start_of_data,),
        binaries(expr),
        (end_of_data,),
        (
            Push(loc(expr), Address(start_of_data, loc(expr))),
            Push(loc(expr), Integer(size(start_of_data), loc(expr))),
            Add(loc(expr))
        )
    )


def const_integral_expr(expr):
    yield Push(loc(expr), Integer(exp(expr), loc(expr)))


def const_float_expr(expr):
    yield Push(loc(expr), Double(exp(expr), loc(expr)))


def const_struct_expr(expr):
    return chain.from_iterable(constant_expression(e) for e in reverse(flatten(exp(expr))))


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
    StringType: const_string_expr,

    StructType: const_struct_expr,
    ArrayType: const_struct_expr,
}
