__author__ = 'samyvilar'

from utils.sequences import peek, consume
from front_end.loader.locations import loc, EOFLocation
from front_end.tokenizer.tokens import TOKENS
from front_end.parser.types import CType, IntegralType, PointerType, c_type, NumericType, IntegerType
from front_end.parser.ast.expressions import SizeOfExpression, UnaryExpression, DereferenceExpression
from front_end.parser.ast.expressions import PrefixIncrementExpression, PrefixDecrementExpression, AddressOfExpression

from front_end.errors import error_if_not_type, error_if_not_value

from front_end.parser.declarations.declarators import type_name


def no_rule_found(tokens, *_):
    raise ValueError('{l} Could not find matching rule for unary_expression got {got}'.format(
        l=loc(peek(tokens, EOFLocation)), got=peek(tokens, '')
    ))


def increment_decrement(tokens, symbol_table, unary_expression):
    operator, unary_exp = consume(tokens), unary_expression(tokens, symbol_table)
    return increment_decrement.rules[operator](unary_exp, c_type(unary_exp)(loc(operator)), loc(operator))
increment_decrement.rules = {
    TOKENS.PLUS_PLUS: PrefixIncrementExpression,
    TOKENS.MINUS_MINUS: PrefixDecrementExpression,
}


def size_of(tokens, symbol_table, unary_expression):
    location = loc(consume(tokens))

    left_parenthesis = None
    if peek(tokens, '') == TOKENS.LEFT_PARENTHESIS:
        left_parenthesis = consume(tokens)

    if peek(tokens, '') in {  # TODO: better organize types.
            TOKENS.VOID, TOKENS.CHAR, TOKENS.SHORT, TOKENS.INT, TOKENS.LONG, TOKENS.FLOAT, TOKENS.DOUBLE,
            TOKENS.STRUCT, TOKENS.SIGNED, TOKENS.UNSIGNED
    } or isinstance(symbol_table.get(peek(tokens, ''), ''), CType):
        ctype = type_name(tokens, symbol_table)
    else:
        ctype = unary_expression(tokens, symbol_table)

    if left_parenthesis:
        _ = error_if_not_value(tokens, TOKENS.RIGHT_PARENTHESIS)

    return SizeOfExpression(ctype, location)


def address_of(cast_exp, operator):
    return AddressOfExpression(cast_exp, PointerType(c_type(cast_exp)(loc(operator)), loc(cast_exp)), loc(operator))


def dereference(cast_exp, operator):
    _ = error_if_not_type(c_type(cast_exp), PointerType)
    return DereferenceExpression(cast_exp, c_type(c_type(cast_exp))(loc(operator)), loc(operator))


def numeric_operator(cast_exp, operator):
    _ = error_if_not_type(c_type(cast_exp), NumericType)
    return UnaryExpression(operator, cast_exp, c_type(cast_exp)(loc(operator)), loc(operator))


def excl_operator(cast_exp, operator):
    _ = error_if_not_type(c_type(cast_exp), NumericType)
    return UnaryExpression(operator, cast_exp, IntegerType(loc(operator)), loc(operator))


def tilde_operator(cast_exp, operator):
    _ = error_if_not_type(c_type(cast_exp), IntegralType)
    return UnaryExpression(operator, cast_exp, c_type(cast_exp)(loc(operator)), loc(operator))


def unary_operator(tokens, symbol_table, cast_expression):
    operator = consume(tokens)
    cast_exp = cast_expression(tokens, symbol_table)
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