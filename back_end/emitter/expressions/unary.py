__author__ = 'samyvilar'

from itertools import chain

from front_end.loader.locations import loc
from front_end.tokenizer.tokens import TOKENS

from front_end.parser.ast.expressions import SizeOfExpression, UnaryExpression, exp, oper, CompoundAssignmentExpression
from front_end.parser.ast.expressions import PrefixIncrementExpression, PrefixDecrementExpression, ConstantExpression
from front_end.parser.ast.expressions import BinaryExpression, DereferenceExpression, AddressOfExpression

from front_end.parser.types import c_type, IntegerType, IntegralType, NumericType, unsigned, CType

from back_end.emitter.c_types import size
from back_end.virtual_machine.instructions.architecture import not_bitwise, load_instr, load_zero_flag, push, Load
from back_end.emitter.expressions.binary import compare_numbers


# Convert Prefix ++exp,--exp operation to (exp += 1) (exp += -1) Compound Assignment Expression
def inc_dec(value, expr, symbol_table, expression_func):
    return expression_func(
        CompoundAssignmentExpression(
            exp(expr),
            TOKENS.PLUS_EQUAL,
            ConstantExpression(value, IntegerType(loc(expr), unsigned=unsigned(c_type(expr))), loc(expr)),
            c_type(expr)(loc(expr)),
            loc(expr)
        ),
        symbol_table,
        expression_func,
    )


def size_of(expr, *_):
    return push(size((isinstance(exp(expr), CType) and exp(expr)) or c_type(exp(expr))), loc(expr))


def address_of(expr, symbol_table, expression_func):
    instrs = expression_func(exp(expr), symbol_table, expression_func)
    value = next(instrs)
    for instr in instrs:
        yield value
        value = instr
    if not isinstance(value, Load):
        yield value


def dereference(expr, symbol_table, expression_func):
    return load_instr(expression_func(exp(expr), symbol_table, expression_func), size(c_type(expr)), loc(expr))


# Convert numeric operator to Binary multiplication operation +expr is 1*expr, -expr is -1*expr
def numeric_operator(value, expr, symbol_table, expression_func):
    return expression_func(
        BinaryExpression(
            ConstantExpression(value, IntegerType(loc(expr)), loc(expr)),
            TOKENS.STAR,
            exp(expr),
            max(c_type(exp(expr)), IntegerType(loc(expr)))(loc(expr)),
            loc(expr),
        ),
        symbol_table,
        expression_func,
    )


def exclamation_operator(expr, symbol_table, expression_func):
    if isinstance(c_type(exp(expr)), IntegralType):
        comp_expr = ConstantExpression(0, c_type(exp(expr))(loc(expr)), loc(expr),)
    elif isinstance(c_type(exp(expr)), NumericType):
        comp_expr = ConstantExpression(0.0, c_type(exp(expr))(loc(expr)), loc(expr),)
    else:
        raise ValueError('{l} exclamation operator only supports numeric types got {g}'.format(
            l=loc(expr), g=c_type(exp(expr))
        ))
    return compare_numbers(
        expression_func(exp(expr), symbol_table, expression_func),
        expression_func(comp_expr, symbol_table, expression_func),
        loc(expr),
        (c_type(expr), c_type(expr), c_type(expr)),
        (load_zero_flag(loc(expr)),)
    )
exclamation_operator.rules = {
    IntegralType: lambda value, location: int(value),
    NumericType: lambda value, location: float(value),
}


def tilde_operator(expr, symbol_table, expression_func):
    return not_bitwise(expression_func(exp(expr), symbol_table, expression_func), loc(oper(expr)))


def unary_operator(expr, symbol_table, expression_func):
    return unary_operator.rules[oper(expr)](expr, symbol_table, expression_func)
unary_operator.rules = {
    TOKENS.AMPERSAND: address_of,
    TOKENS.STAR: dereference,

    TOKENS.PLUS: lambda *args: numeric_operator(1, *args),
    TOKENS.MINUS: lambda *args: numeric_operator(-1, *args),
    TOKENS.EXCLAMATION: exclamation_operator,

    TOKENS.TILDE: tilde_operator,
}


def unary_expression(expr, symbol_table, expression_func):
    return unary_expression.rules[type(expr)](expr, symbol_table, expression_func)
unary_expression.rules = {
    SizeOfExpression: size_of,
    PrefixIncrementExpression: lambda *args: inc_dec(1, *args),
    PrefixDecrementExpression: lambda *args: inc_dec(-1, *args),

    AddressOfExpression: unary_operator,

    UnaryExpression: unary_operator,
    DereferenceExpression: unary_operator,
}