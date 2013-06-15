__author__ = 'samyvilar'

from front_end.loader.locations import loc
from front_end.tokenizer.tokens import TOKENS
from front_end.parser.types import CType, IntegralType, PointerType, c_type, NumericType, IntegerType
from front_end.parser.ast.expressions import SizeOfExpression, UnaryExpression, DereferenceExpression
from front_end.parser.ast.expressions import PrefixIncrementExpression, PrefixDecrementExpression

from front_end.errors import error_if_not_lvalue, error_if_not_type, error_if_not_value


def no_rule_found(tokens, *_):
    raise ValueError('{l} Could not find matching rule for {got} for unary_expression'.format(
        l=loc(tokens[0]), got=tokens[0]))


def increment_decrement(tokens, symbol_table, unary_expression):
    operator, unary_exp = tokens.pop(0), unary_expression(tokens, symbol_table)
    location = loc(operator)
    error_if_not_lvalue(unary_exp, operator)
    _ = error_if_not_type([c_type(unary_exp)], IntegralType)
    return increment_decrement.rules[operator](unary_exp, c_type(unary_exp)(location), location)
increment_decrement.rules = {
    TOKENS.PLUS_PLUS: PrefixIncrementExpression,
    TOKENS.MINUS_MINUS: PrefixDecrementExpression,
}


def size_of(tokens, symbol_table, unary_expression):
    location = loc(tokens.pop(0))

    left_parenthesis = None
    if tokens[0] == TOKENS.LEFT_PARENTHESIS:
        left_parenthesis = tokens.pop(0)

    if isinstance(symbol_table.get(tokens[0]), CType):  # Symbol Table should be initialized with default types.
        ctype = symbol_table[tokens.pop(0)]
    else:
        ctype = unary_expression(tokens, symbol_table)

    if left_parenthesis:
        _ = error_if_not_value(tokens, TOKENS.RIGHT_PARENTHESIS)

    return SizeOfExpression(ctype, location)


def address_of(cast_exp, operator):
    error_if_not_lvalue(cast_exp, operator)
    return UnaryExpression(
        operator, cast_exp, PointerType(c_type(cast_exp)(loc(operator)), loc(cast_exp)), loc(operator)
    )


def dereference(cast_exp, operator):
    _ = error_if_not_type([c_type(cast_exp)], PointerType)
    return DereferenceExpression(cast_exp, c_type(c_type(cast_exp))(loc(operator)), loc(operator))


def numeric_operator(cast_exp, operator):
    _ = error_if_not_type([c_type(cast_exp)], NumericType)
    return UnaryExpression(operator, cast_exp, c_type(cast_exp)(loc(operator)), loc(operator))


def excl_operator(cast_exp, operator):
    _ = error_if_not_type([c_type(cast_exp)], NumericType)
    return UnaryExpression(operator, cast_exp, IntegerType(loc(operator)), loc(operator))


def tilde_operator(cast_exp, operator):
    _ = error_if_not_type([c_type(cast_exp)], IntegralType)
    return UnaryExpression(operator, cast_exp, c_type(cast_exp)(loc(operator)), loc(operator))


def unary_operator(tokens, symbol_table, cast_expression):
    operator, cast_exp = tokens.pop(0), cast_expression(tokens, symbol_table)
    # noinspection PyUnresolvedReferences
    return unary_operator.rules[operator](cast_exp, operator)
unary_operator.rules = {
    TOKENS.AMPERSAND: address_of,
    TOKENS.STAR: dereference,

    TOKENS.PLUS: numeric_operator,
    TOKENS.MINUS: numeric_operator,
    TOKENS.EXCLAMATION: excl_operator,

    TOKENS.TILDE: tilde_operator,
}