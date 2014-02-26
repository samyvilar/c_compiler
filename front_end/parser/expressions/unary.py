__author__ = 'samyvilar'

from itertools import chain, izip, repeat

from utils.sequences import peek, consume, peek_or_terminal
from front_end.loader.locations import loc
from utils.rules import rules, set_rules
from front_end.tokenizer.tokens import TOKENS, IDENTIFIER, CONSTANT
from front_end.parser.types import IntegralType, PointerType, c_type, NumericType, logical_type
from front_end.parser.types import void_pointer_type
from front_end.parser.ast.expressions import SizeOfExpression, UnaryExpression, DereferenceExpression
from front_end.parser.ast.expressions import PrefixIncrementExpression, PrefixDecrementExpression, AddressOfExpression
from front_end.parser.ast.expressions import AddressOfLabelExpression

from front_end.parser.expressions.reduce import reduce_expression
from front_end.parser.expressions.cast import type_name_or_unary_expression

from utils.errors import error_if_not_type, error_if_empty


def increment_decrement(tokens, symbol_table):
    operator, unary_exp = consume(tokens), symbol_table['__ unary_expression __'](tokens, symbol_table)
    return rules(increment_decrement)[operator](unary_exp, c_type(unary_exp)(loc(operator)), loc(operator))
set_rules(
    increment_decrement,
    ((TOKENS.PLUS_PLUS, PrefixIncrementExpression), (TOKENS.MINUS_MINUS, PrefixDecrementExpression))
)


def size_of(tokens, symbol_table):  # 'sizeof' unary_expression | '(' type_name ')'
    location = loc(consume(tokens))
    return SizeOfExpression(type_name_or_unary_expression(tokens, symbol_table), location)


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
    return UnaryExpression(operator, cast_exp, logical_type(loc(operator)), loc(operator))


def tilde_operator(cast_exp, operator):
    _ = error_if_not_type(c_type(cast_exp), IntegralType)
    return UnaryExpression(operator, cast_exp, c_type(cast_exp)(loc(operator)), loc(operator))


def address_of_label(tokens, symbol_table):
    operator = consume(tokens)
    return AddressOfLabelExpression(
        error_if_not_type(consume(tokens, ''), IDENTIFIER), void_pointer_type(loc(operator)), loc(operator)
    )


def unary_operator(tokens, symbol_table):
    operator = consume(tokens)
    if operator == TOKENS.LOGICAL_AND:
        return AddressOfLabelExpression(
            error_if_not_type(consume(tokens, ''), IDENTIFIER), void_pointer_type(loc(operator)), loc(operator)
        )
    cast_exp = symbol_table['__ cast_expression __'](tokens, symbol_table)
    return rules(unary_operator)[operator](cast_exp, operator)
set_rules(
    unary_operator,
    (
        (TOKENS.LOGICAL_AND, address_of),
        (TOKENS.AMPERSAND, address_of),
        (TOKENS.STAR, dereference),

        (TOKENS.PLUS, numeric_operator),
        (TOKENS.MINUS, numeric_operator),
        (TOKENS.EXCLAMATION, excl_operator),

        (TOKENS.TILDE, tilde_operator),
    )
)


@reduce_expression
def unary_expression(tokens, symbol_table):
    """
        :   postfix_expression
            | '++' unary_expression
            | '--' unary_expression
            | unary_operator cast_expression
            | 'sizeof' (type_name | unary_expression)
    """
    error_if_empty(tokens)

    if peek_or_terminal(tokens) in rules(unary_expression) and not isinstance(peek(tokens), CONSTANT):
        return rules(unary_expression)[peek(tokens)](tokens, symbol_table)

    return symbol_table['__ postfix_expression __'](tokens, symbol_table)
set_rules(
    unary_expression,
    chain(
        izip(rules(unary_operator), repeat(unary_operator)),
        (
            (TOKENS.PLUS_PLUS, increment_decrement),
            (TOKENS.MINUS_MINUS, increment_decrement),
            (TOKENS.SIZEOF, size_of),
        )
    )
)