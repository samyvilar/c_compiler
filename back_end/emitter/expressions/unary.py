__author__ = 'samyvilar'

from itertools import chain, izip_longest

from front_end.loader.locations import loc
from front_end.tokenizer.tokens import TOKENS

from front_end.parser.ast.expressions import SizeOfExpression, UnaryExpression, exp, oper, CompoundAssignmentExpression
from front_end.parser.ast.expressions import PrefixIncrementExpression, PrefixDecrementExpression, ConstantExpression
from front_end.parser.ast.expressions import BinaryExpression, DereferenceExpression, AddressOfExpression

from front_end.parser.types import c_type, base_c_type, IntegerType, IntegralType, NumericType

from back_end.emitter.types import size
from back_end.virtual_machine.instructions.architecture import Push, Not, Load, Integer, LoadZeroFlag, Double
from back_end.emitter.expressions.binary import compare_numbers


# Convert Prefix ++exp,--exp operation to (exp += 1) (exp += -1) Compound Assignment Expression
def inc_dec(value, expr, symbol_table, expression_func):
    return expression_func(
        CompoundAssignmentExpression(
            exp(expr),
            TOKENS.PLUS_EQUAL,
            ConstantExpression(value, IntegerType(loc(expr)), loc(expr)),
            c_type(expr)(loc(expr)),
            loc(expr)
        ),
        symbol_table,
        expression_func,
    )


def size_of(expr, *_):
    yield Push(loc(expr), size(c_type(exp(expr))))


def address_of(expr, symbol_table, expression_func):
    instrs = expression_func(exp(expr), symbol_table, expression_func)
    value = next(instrs)
    for instr in instrs:
        yield value
        value = instr
    if not isinstance(value, Load):
        yield value


def dereference(expr, symbol_table, expression_func):
    return chain(
        expression_func(exp(expr), symbol_table, expression_func), (Load(loc(expr), size(c_type(expr))),)
    )


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
    return chain(
        compare_numbers(
            expression_func(exp(expr), symbol_table, expression_func),
            (Push(loc(expr), exclamation_operator.rules[base_c_type(c_type(exp(expr)))](0, loc(expr))),),
            loc(expr),
            c_type(expr),
        ),
        (LoadZeroFlag(loc(expr)),)
    )
exclamation_operator.rules = {
    IntegralType: lambda value, location: Integer(int(value), location),
    NumericType: lambda value, location: Double(float(value), location),
}


def tilde_operator(expr, symbol_table, expression_func):
    return chain(expression_func(exp(expr), symbol_table, expression_func), (Not(loc(oper(expr))),))


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