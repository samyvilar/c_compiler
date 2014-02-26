__author__ = 'samyvilar'

from itertools import chain

from utils.rules import set_rules, rules
from front_end.loader.locations import loc
from front_end.tokenizer.tokens import TOKENS

from front_end.parser.ast.expressions import SizeOfExpression, UnaryExpression, exp, oper, CompoundAssignmentExpression
from front_end.parser.ast.expressions import PrefixIncrementExpression, PrefixDecrementExpression, ConstantExpression
from front_end.parser.ast.expressions import BinaryExpression, DereferenceExpression, AddressOfExpression

from front_end.parser.types import c_type, IntegerType, IntegralType, NumericType, unsigned, CType, ArrayType

from back_end.emitter.c_types import size, size_arrays_as_pointers
from back_end.virtual_machine.instructions.architecture import load, load_zero_flag, Loads, get_compare
from back_end.virtual_machine.instructions.architecture import get_not_bitwise


# Convert Prefix ++exp,--exp operation to (exp += 1) (exp += -1) Compound Assignment Expression
def inc_dec(value, expr, symbol_table):
    return symbol_table['__ expression __'](
        CompoundAssignmentExpression(
            exp(expr),
            TOKENS.PLUS_EQUAL,
            ConstantExpression(value, IntegerType(loc(expr), unsigned=unsigned(c_type(expr))), loc(expr)),
            c_type(expr)(loc(expr)),
            loc(expr)
        ),
        symbol_table,
    )


def size_of(expr, symbol_table):
    ctype = exp(expr) if isinstance(exp(expr), CType) else c_type(exp(expr))
    return symbol_table['__ expression __'](ConstantExpression(size(ctype), c_type(expr), loc(expr)), symbol_table)


def address_of(expr, symbol_table):
    instrs = symbol_table['__ expression __'](exp(expr), symbol_table)
    value = next(instrs)
    for instr in instrs:
        yield value
        value = instr
    if not isinstance(value, Loads):
        yield value


def dereference(expr, symbol_table):
    return load(
        symbol_table['__ expression __'](exp(expr), symbol_table), size_arrays_as_pointers(c_type(expr)), loc(expr)
    )


# Convert numeric operator to Binary multiplication operation +expr is 1*expr, -expr is -1*expr
def numeric_operator(value, expr, symbol_table):
    return symbol_table['__ expression __'](
        BinaryExpression(
            ConstantExpression(value, IntegerType(loc(expr)), loc(expr)),
            TOKENS.STAR,
            exp(expr),
            max(c_type(exp(expr)), IntegerType(loc(expr)))(loc(expr)),
            loc(expr),
        ),
        symbol_table,
    )


def exclamation_operator(expr, symbol_table):
    if not isinstance(c_type(exp(expr)), NumericType):
        raise ValueError('{l} exclamation operator only supports numeric types got {g}'.format(
            l=loc(expr), g=c_type(exp(expr))
        ))
    assert not isinstance(c_type(exp(expr)), ArrayType)
    expression = symbol_table['__ expression __']
    return get_compare(size_arrays_as_pointers(c_type(exp(expr))))(
        expression(exp(expr), symbol_table),
        expression(ConstantExpression(0, c_type(exp(expr))(loc(expr)), loc(expr),), symbol_table),
        loc(expr),
        (load_zero_flag(loc(expr)),)
    )
# exclamation_operator.rules = {
#     IntegralType: lambda value, location: int(value),
#     NumericType: lambda value, location: float(value),
# }


def tilde_operator(expr, symbol_table):
    return get_not_bitwise(size_arrays_as_pointers(c_type(expr)))(
        symbol_table['__ expression __'](exp(expr), symbol_table), loc(oper(expr))
    )


def unary_operator(expr, symbol_table):
    return rules(unary_operator)[oper(expr)](expr, symbol_table)
set_rules(
    unary_operator,
    (
        (TOKENS.AMPERSAND, address_of),
        (TOKENS.STAR, dereference),

        (TOKENS.PLUS, lambda *args: numeric_operator(1, *args)),
        (TOKENS.MINUS, lambda *args: numeric_operator(-1, *args)),
        (TOKENS.EXCLAMATION, exclamation_operator),

        (TOKENS.TILDE, tilde_operator),
    )
)


def unary_expression(expr, symbol_table):
    return rules(unary_expression)[type(expr)](expr, symbol_table)
set_rules(
    unary_expression,
    (
        (SizeOfExpression, size_of),
        (PrefixIncrementExpression, lambda *args: inc_dec(1, *args)),
        (PrefixDecrementExpression, lambda *args: inc_dec(-1, *args)),

        (AddressOfExpression, unary_operator),
        (UnaryExpression, unary_operator),
        (DereferenceExpression, unary_operator),
    )
)
