__author__ = 'samyvilar'

from itertools import chain, imap, izip, repeat

from utils.sequences import peek, consume_all, reverse, flatten
from utils.rules import rules, set_rules

from front_end.loader.locations import loc
from back_end.emitter.expressions.static import static_binaries
from front_end.parser.ast.expressions import exp
from front_end.parser.types import FloatType, DoubleType
from front_end.parser.types import StringType, c_type, StructType, ArrayType, UnionType, integral_types
from back_end.virtual_machine.instructions.architecture import push, Double, Address, relative_jump, Offset
from back_end.virtual_machine.instructions.architecture import allocate, get_push, DoubleHalf
from back_end.emitter.c_types import size


def const_string_expr(expr):  # strings are embedded ...
    data = static_binaries(expr)
    _initial_data = peek(data)  # there should be at least one char, '\0'
    _push = push(Address(_initial_data, loc(expr)), loc(expr))
    return chain(relative_jump(Offset(peek(_push, loc(expr)), loc(expr)), loc(expr)), consume_all(data, _push))


def const_integral_expr(expr):
    return get_push(size(c_type(expr)))(exp(expr), loc(expr))


def const_float_expr(expr):
    return get_push(size(c_type(expr)))(DoubleHalf(exp(expr), loc(expr)), loc(expr))


def const_double_expr(expr):
    return get_push(size(c_type(expr)))(Double(exp(expr), loc(expr)), loc(expr))


def const_struct_expr(expr):
    return chain.from_iterable(imap(constant_expression, reverse(flatten(exp(expr)))))


def const_union_expr(expr):
    assert len(exp(expr)) <= 1
    return chain(                   # allocate rest ...
        allocate(size(c_type(expr)) - sum(imap(size, imap(c_type, exp(expr)))), loc(expr)),
        const_struct_expr(exp(expr))
    )


def constant_expression(expr, *_):
    return rules(constant_expression)[type(c_type(expr))](expr)
set_rules(
    constant_expression,
    chain(
        izip(integral_types, repeat(const_integral_expr)),
        (
            (FloatType, const_float_expr),
            (DoubleType, const_double_expr),

            (UnionType, const_union_expr),
            (StructType, const_struct_expr),
            (ArrayType, const_struct_expr),

            (StringType, const_string_expr),
        )
    )
)
