__author__ = 'samyvilar'

from front_end.loader.locations import loc
from front_end.tokenizer.tokens import TOKENS

from front_end.parser.types import NumericType, IntegralType, c_type, safe_type_coercion

from front_end.parser.ast.expressions import BinaryExpression, AssignmentExpression, CompoundAssignmentExpression, oper
from front_end.parser.ast.expressions import left_exp, right_exp
from front_end.parser.expressions.reduce import reduce_expression

from front_end.errors import error_if_not_type, error_if_not_lvalue


@reduce_expression
def get_binary_expression(tokens, symbol_table, l_exp, right_exp_func, exp_type, cast_expression):
    operator = tokens.pop(0)
    if right_exp_func == cast_expression:
        r_exp = right_exp_func(tokens, symbol_table)
    else:
        r_exp = right_exp_func(tokens, symbol_table, cast_expression)
    exp_type = max(error_if_not_type([c_type(l_exp)], exp_type), error_if_not_type([c_type(r_exp)], exp_type))
    return BinaryExpression(l_exp, operator, r_exp, exp_type(loc(operator)), loc(operator))


def multiplicative_expression(tokens, symbol_table, cast_expression):
    # : cast_expression ('*' cast_expression | '/' cast_expression | '%' cast_expression)*
    exp = cast_expression(tokens, symbol_table)
    while tokens and tokens[0] in {TOKENS.STAR, TOKENS.PERCENTAGE, TOKENS.FORWARD_SLASH}:
        # noinspection PyUnresolvedReferences
        exp = multiplicative_expression.rules[tokens[0]](tokens, symbol_table, exp, cast_expression)
    return exp
multiplicative_expression.rules = {
    TOKENS.STAR:
    lambda t, s, exp, cast_expression: get_binary_expression(t, s, exp, cast_expression, NumericType, cast_expression),

    TOKENS.PERCENTAGE:
    lambda t, s, exp, cast_expression: get_binary_expression(t, s, exp, cast_expression, IntegralType, cast_expression),

    TOKENS.FORWARD_SLASH:
    lambda t, s, exp, cast_expression: get_binary_expression(t, s, exp, cast_expression, NumericType, cast_expression),
}


def additive_expression(tokens, symbol_table, cast_expression):
    # : multiplicative_expression ('+' multiplicative_expression | '-' multiplicative_expression)*
    exp = multiplicative_expression(tokens, symbol_table, cast_expression)
    while tokens and tokens[0] in {TOKENS.PLUS, TOKENS.MINUS}:
        exp = get_binary_expression(tokens, symbol_table, exp, multiplicative_expression, NumericType, cast_expression)
    return exp


def shift_expression(tokens, symbol_table, cast_expression):
    # : additive_expression (('<<'|'>>') additive_expression)*
    exp = additive_expression(tokens, symbol_table, cast_expression)
    while tokens and tokens[0] in {TOKENS.SHIFT_LEFT, TOKENS.SHIFT_RIGHT}:
        exp = get_binary_expression(tokens, symbol_table, exp, additive_expression, IntegralType, cast_expression)
    return exp


def relational_expression(tokens, symbol_table, cast_expression):
    # : shift_expression (('<'|'>'|'<='|'>=') shift_expression)*
    exp = shift_expression(tokens, symbol_table, cast_expression)
    while tokens and tokens[0] in \
            {TOKENS.LESS_THAN, TOKENS.GREATER_THAN, TOKENS.LESS_THAN_OR_EQUAL, TOKENS.GREATER_THAN_OR_EQUAL}:
        exp = get_binary_expression(tokens, symbol_table, exp, shift_expression, NumericType, cast_expression)
    return exp


def equality_expression(tokens, symbol_table, cast_expression):
    # : relational_expression (('=='|'!=') relational_expression)*
    exp = relational_expression(tokens, symbol_table, cast_expression)
    while tokens and tokens[0] in {TOKENS.EQUAL_EQUAL, TOKENS.NOT_EQUAL}:
        exp = get_binary_expression(tokens, symbol_table, exp, relational_expression, NumericType, cast_expression)
    return exp


def and_expression(tokens, symbol_table, cast_expression):
    # : equality_expression ('&' equality_expression)*
    exp = equality_expression(tokens, symbol_table, cast_expression)
    while tokens and tokens[0] == TOKENS.AMPERSAND:
        exp = get_binary_expression(tokens, symbol_table, exp, equality_expression, IntegralType, cast_expression)
    return exp


def exclusive_or_expression(tokens, symbol_table, cast_expression):
    # : and_expression ('^' and_expression)*
    exp = and_expression(tokens, symbol_table, cast_expression)
    while tokens and tokens[0] == TOKENS.CARET:
        exp = get_binary_expression(tokens, symbol_table, exp, and_expression, IntegralType, cast_expression)
    return exp


def inclusive_or_expression(tokens, symbol_table, cast_expression):
    # : exclusive_or_expression ('|' exclusive_or_expression)*
    exp = exclusive_or_expression(tokens, symbol_table, cast_expression)
    while tokens and tokens[0] == TOKENS.BAR:
        exp = get_binary_expression(tokens, symbol_table, exp, exclusive_or_expression, IntegralType, cast_expression)
    return exp


def logical_and_expression(tokens, symbol_table, cast_expression):
    # : inclusive_or_expression ('&&' inclusive_or_expression)*
    exp = inclusive_or_expression(tokens, symbol_table, cast_expression)
    while tokens and tokens[0] == TOKENS.LOGICAL_AND:
        exp = get_binary_expression(tokens, symbol_table, exp, inclusive_or_expression, NumericType, cast_expression)
    return exp


def logical_or_expression(tokens, symbol_table, cast_expression):
    # : logical_and_expression ('||' logical_and_expression)*
    exp = logical_and_expression(tokens, symbol_table, cast_expression)
    while tokens and tokens[0] == TOKENS.LOGICAL_OR:
        exp = get_binary_expression(tokens, symbol_table, exp, logical_and_expression, NumericType, cast_expression)
    return exp


def numeric_type(tokens, symbol_table, l_exp, cast_expression):
    exp = get_binary_expression(tokens, symbol_table, l_exp, assignment_expression, NumericType, cast_expression)
    return CompoundAssignmentExpression(left_exp(exp), oper(exp), right_exp(exp), c_type(exp)(loc(exp)), loc(exp))


def integral_type(tokens, symbol_table, l_exp, cast_expression):
    exp = get_binary_expression(tokens, symbol_table, l_exp, assignment_expression, IntegralType, cast_expression)
    return CompoundAssignmentExpression(left_exp(exp), oper(exp), right_exp(exp), c_type(exp)(loc(exp)), loc(exp))


def assign(tokens, symbol_table, l_exp, cast_expression):
    operator = tokens.pop(0)
    r_exp = assignment_expression(tokens, symbol_table, cast_expression)

    if not safe_type_coercion(c_type(l_exp), c_type(r_exp)):
        raise ValueError('{l} Cannot assign incompatible types {to_type} {from_type}'.format(
            l=loc(operator), from_type=c_type(r_exp), to_type=c_type(l_exp),
        ))
    return AssignmentExpression(l_exp, operator, r_exp, c_type(l_exp)(loc(oper)), loc(oper))


def assignment_expression(tokens, symbol_table, cast_expression):
    # : logical_or_expression | logical_or_expression assignment_operator assignment_expression
    left_value_exp = logical_or_expression(tokens, symbol_table, cast_expression)
    # noinspection PyUnresolvedReferences
    if tokens and tokens[0] in assignment_expression.rules:
        error_if_not_lvalue(left_value_exp, tokens[0])
        # noinspection PyUnresolvedReferences
        return assignment_expression.rules[tokens[0]](tokens, symbol_table, left_value_exp, cast_expression)
    return left_value_exp
assignment_expression.rules = {
    TOKENS.EQUAL: assign,                        # '=',

    TOKENS.STAR_EQUAL: numeric_type,             # '*=',
    TOKENS.FORWARD_SLASH_EQUAL: numeric_type,    # '/=',
    TOKENS.PERCENTAGE_EQUAL: integral_type,      # '%=',
    TOKENS.PLUS_EQUAL: numeric_type,             # '+=',
    TOKENS.MINUS_EQUAL: numeric_type,            # '-=',
    TOKENS.SHIFT_LEFT_EQUAL: integral_type,      # '<<=',
    TOKENS.SHIFT_RIGHT_EQUAL: integral_type,     # '>>=',
    TOKENS.AMPERSAND_EQUAL: integral_type,       # '&=',
    TOKENS.CARET_EQUAL: integral_type,           # '^=',
    TOKENS.BAR_EQUAL: integral_type,             # '|=',
}