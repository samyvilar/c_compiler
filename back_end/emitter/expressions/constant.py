__author__ = 'samyvilar'

from itertools import chain, imap

from utils.sequences import peek, takewhile
from utils.sequences import reverse, flatten
from front_end.loader.locations import loc
from back_end.emitter.c_types import binaries
from front_end.parser.ast.expressions import exp
from front_end.parser.types import CharType, ShortType, IntegerType, LongType, FloatType, DoubleType, PointerType
from front_end.parser.types import StringType, c_type, StructType, ArrayType, UnionType
from back_end.virtual_machine.instructions.architecture import push, Double, Address, Pass, relative_jump, Offset
from back_end.virtual_machine.instructions.architecture import allocate
from back_end.emitter.c_types import size


def const_string_expr(expr):
    data = binaries(expr)
    try:
        _initial_data = peek(data)
    except StopIteration:
        _initial_data = Pass(loc(expr))
        data = (_initial_data,)

    _push = push(Address(_initial_data, loc(expr)), loc(expr))

    return chain(
        relative_jump(Offset(peek(_push, loc(expr)), loc(expr)), loc(expr)),
        takewhile(None, data),
        takewhile(None, _push)
    )


def const_integral_expr(expr):
    return push(exp(expr), loc(expr))


def const_float_expr(expr):
    return push(Double(exp(expr), loc(expr)), loc(expr))


def const_struct_expr(expr):
    return chain.from_iterable(imap(constant_expression, reverse(flatten(exp(expr)))))


def const_union_expr(expr):
    return chain(
        allocate(size(c_type(expr)) - sum(imap(size, imap(c_type, exp(expr)))), loc(expr)),  # allocate rest ...
        const_struct_expr(expr),

    )


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

    UnionType: const_union_expr,
    StructType: const_struct_expr,
    ArrayType: const_struct_expr,
}
