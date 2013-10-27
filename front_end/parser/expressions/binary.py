__author__ = 'samyvilar'

from sequences import peek, consume
from front_end.loader.locations import loc
from front_end.tokenizer.tokens import TOKENS

from front_end.parser.types import NumericType, IntegralType, c_type, safe_type_coercion, supported_operators
from front_end.parser.types import LOGICAL_OPERATIONS, IntegerType, PointerType

from front_end.parser.ast.expressions import BinaryExpression, AssignmentExpression, CompoundAssignmentExpression, oper
from front_end.parser.ast.expressions import TernaryExpression, left_exp, right_exp, SizeOfExpression
from front_end.parser.expressions.reduce import reduce_expression

from front_end.errors import error_if_not_type, error_if_not_value


@reduce_expression
def get_binary_expression(tokens, symbol_table, l_exp, right_exp_func, exp_type, cast_expression):
    operator = consume(tokens)

    if right_exp_func == cast_expression:
        r_exp = right_exp_func(tokens, symbol_table)
    else:
        r_exp = right_exp_func(tokens, symbol_table, cast_expression)

    exp_type = max(error_if_not_type(c_type(l_exp), exp_type), error_if_not_type(c_type(r_exp), exp_type))
    if operator in LOGICAL_OPERATIONS:
        exp_type = IntegerType

    if operator not in supported_operators(c_type(l_exp)):
        raise ValueError('{l} ctype {g} does not support {o}'.format(l=loc(l_exp), g=c_type(l_exp), o=operator))
    if operator not in supported_operators(c_type(r_exp)):
        raise ValueError('{l} ctype {g} does not support {o}'.format(l=loc(r_exp), g=c_type(r_exp), o=operator))

    return BinaryExpression(l_exp, operator, r_exp, exp_type(loc(operator)), loc(operator))


def multiplicative_expression(tokens, symbol_table, cast_expression):
    # : cast_expression ('*' cast_expression | '/' cast_expression | '%' cast_expression)*
    exp = cast_expression(tokens, symbol_table)
    while peek(tokens, '') in {TOKENS.STAR, TOKENS.PERCENTAGE, TOKENS.FORWARD_SLASH}:
        # noinspection PyUnresolvedReferences
        exp = multiplicative_expression.rules[peek(tokens)](tokens, symbol_table, exp, cast_expression)
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
    while peek(tokens, '') in {TOKENS.PLUS, TOKENS.MINUS}:
        exp = get_binary_expression(tokens, symbol_table, exp, multiplicative_expression, NumericType, cast_expression)
    return exp


def shift_expression(tokens, symbol_table, cast_expression):
    # : additive_expression (('<<'|'>>') additive_expression)*
    exp = additive_expression(tokens, symbol_table, cast_expression)
    while peek(tokens, '') in {TOKENS.SHIFT_LEFT, TOKENS.SHIFT_RIGHT}:
        exp = get_binary_expression(tokens, symbol_table, exp, additive_expression, IntegralType, cast_expression)
    return exp


def relational_expression(tokens, symbol_table, cast_expression):
    # : shift_expression (('<'|'>'|'<='|'>=') shift_expression)*
    exp = shift_expression(tokens, symbol_table, cast_expression)
    while peek(tokens, '') in {
        TOKENS.LESS_THAN, TOKENS.GREATER_THAN, TOKENS.LESS_THAN_OR_EQUAL, TOKENS.GREATER_THAN_OR_EQUAL
    }:
        exp = get_binary_expression(tokens, symbol_table, exp, shift_expression, NumericType, cast_expression)
    return exp


def equality_expression(tokens, symbol_table, cast_expression):
    # : relational_expression (('=='|'!=') relational_expression)*
    exp = relational_expression(tokens, symbol_table, cast_expression)
    while peek(tokens, '') in {TOKENS.EQUAL_EQUAL, TOKENS.NOT_EQUAL}:
        exp = get_binary_expression(tokens, symbol_table, exp, relational_expression, NumericType, cast_expression)
    return exp


def and_expression(tokens, symbol_table, cast_expression):
    # : equality_expression ('&' equality_expression)*
    exp = equality_expression(tokens, symbol_table, cast_expression)
    while peek(tokens, '') == TOKENS.AMPERSAND:
        exp = get_binary_expression(tokens, symbol_table, exp, equality_expression, IntegralType, cast_expression)
    return exp


def exclusive_or_expression(tokens, symbol_table, cast_expression):
    # : and_expression ('^' and_expression)*
    exp = and_expression(tokens, symbol_table, cast_expression)
    while peek(tokens, '') == TOKENS.CARET:
        exp = get_binary_expression(tokens, symbol_table, exp, and_expression, IntegralType, cast_expression)
    return exp


def inclusive_or_expression(tokens, symbol_table, cast_expression):
    # : exclusive_or_expression ('|' exclusive_or_expression)*
    exp = exclusive_or_expression(tokens, symbol_table, cast_expression)
    while peek(tokens, '') == TOKENS.BAR:
        exp = get_binary_expression(tokens, symbol_table, exp, exclusive_or_expression, IntegralType, cast_expression)
    return exp


def logical_and_expression(tokens, symbol_table, cast_expression):
    # : inclusive_or_expression ('&&' inclusive_or_expression)*
    exp = inclusive_or_expression(tokens, symbol_table, cast_expression)
    while peek(tokens, '') == TOKENS.LOGICAL_AND:
        exp = get_binary_expression(tokens, symbol_table, exp, inclusive_or_expression, NumericType, cast_expression)
    return exp


def logical_or_expression(tokens, symbol_table, cast_expression):
    # : logical_and_expression ('||' logical_and_expression)*
    exp = logical_and_expression(tokens, symbol_table, cast_expression)
    while peek(tokens, '') == TOKENS.LOGICAL_OR:
        exp = get_binary_expression(tokens, symbol_table, exp, logical_and_expression, NumericType, cast_expression)
    return exp


def conditional_expression(tokens, symbol_table, cast_expression):
    # logical_or_expression ('?' expression ':' conditional_expression)?
    exp = logical_or_expression(tokens, symbol_table, cast_expression)
    if peek(tokens, '') in conditional_expression.rules:
        location = loc(error_if_not_value(tokens, TOKENS.QUESTION))
        _ = error_if_not_type(c_type(exp), NumericType)
        if_true_exp = assignment_expression(tokens, symbol_table, cast_expression)
        _ = error_if_not_value(tokens, TOKENS.COLON)
        if_false_exp = conditional_expression(tokens, symbol_table, cast_expression)

        ctype_1, ctype_2 = c_type(if_true_exp), c_type(if_false_exp)
        if safe_type_coercion(ctype_1, ctype_2):
            ctype = ctype_1(location)
        elif safe_type_coercion(ctype_2, ctype_1):
            ctype = ctype_2(location)
        else:
            raise ValueError('{l} Could not determine type for ternary-expr, giving the types {t1} and {t2}'.format(
                t1=ctype_1, t2=ctype_2
            ))
        return TernaryExpression(exp, if_true_exp, if_false_exp, ctype, location)
    else:
        return exp
conditional_expression.rules = {TOKENS.QUESTION}


def numeric_type(tokens, symbol_table, l_exp, cast_expression):
    exp = get_binary_expression(tokens, symbol_table, l_exp, assignment_expression, NumericType, cast_expression)
    return CompoundAssignmentExpression(left_exp(exp), oper(exp), right_exp(exp), c_type(exp)(loc(exp)), loc(exp))


def integral_type(tokens, symbol_table, l_exp, cast_expression):
    exp = get_binary_expression(tokens, symbol_table, l_exp, assignment_expression, IntegralType, cast_expression)
    return CompoundAssignmentExpression(left_exp(exp), oper(exp), right_exp(exp), c_type(exp)(loc(exp)), loc(exp))


def assign(tokens, symbol_table, l_exp, cast_expression):
    operator, r_exp = consume(tokens), assignment_expression(tokens, symbol_table, cast_expression)
    return AssignmentExpression(l_exp, operator, r_exp, c_type(l_exp)(loc(oper)), loc(operator))


def assignment_expression(tokens, symbol_table, cast_expression):
    # : conditional_expression | conditional_expression assignment_operator assignment_expression
    left_value_exp = conditional_expression(tokens, symbol_table, cast_expression)
    if peek(tokens, '') in assignment_expression.rules:
        return assignment_expression.rules[peek(tokens)](tokens, symbol_table, left_value_exp, cast_expression)
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