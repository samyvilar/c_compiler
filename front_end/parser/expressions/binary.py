__author__ = 'samyvilar'

from itertools import imap, repeat

from utils.rules import rules
from utils.sequences import peek, consume

from front_end.loader.locations import loc
from front_end.tokenizer.tokens import TOKENS

from front_end.parser.types import NumericType, IntegralType, c_type, safe_type_coercion, supported_operations
from front_end.parser.types import LOGICAL_OPERATIONS, LongType, PointerType, logical_type

from front_end.parser.ast.expressions import BinaryExpression, AssignmentExpression, CompoundAssignmentExpression, oper
from front_end.parser.ast.expressions import TernaryExpression, left_exp, right_exp
from front_end.parser.expressions.reduce import reduce_expression

from utils.errors import error_if_not_type, error_if_not_value


@reduce_expression
def get_binary_expression(tokens, symbol_table, l_exp, right_exp_func, exp_type):
    operator = consume(tokens)
    r_exp = right_exp_func(tokens, symbol_table)

    exp_type = max(imap(error_if_not_type, imap(c_type, (l_exp, r_exp)), repeat(exp_type)))
    if operator in LOGICAL_OPERATIONS:
        exp_type = logical_type

    if operator not in supported_operations(c_type(l_exp)):
        raise ValueError('{l} ctype {g} does not support {o}'.format(l=loc(l_exp), g=c_type(l_exp), o=operator))
    if operator not in supported_operations(c_type(r_exp)):
        raise ValueError('{l} ctype {g} does not support {o}'.format(l=loc(r_exp), g=c_type(r_exp), o=operator))

    return BinaryExpression(l_exp, operator, r_exp, exp_type(location=loc(operator)), loc(operator))


def multiplicative_expression(tokens, symbol_table):
    # : cast_expression ('*' cast_expression | '/' cast_expression | '%' cast_expression)*
    cast_expression = symbol_table['__ cast_expression __']
    exp = cast_expression(tokens, symbol_table)
    while peek(tokens, '') in rules(multiplicative_expression):
        exp = get_binary_expression(
            tokens, symbol_table, exp, cast_expression, rules(multiplicative_expression)[peek(tokens)]
        )
    return exp
multiplicative_expression.rules = {
    TOKENS.STAR: NumericType,
    TOKENS.PERCENTAGE: IntegralType,
    TOKENS.FORWARD_SLASH: NumericType
}


def is_binary_pointer_expression(_exp):
    return all(imap(
        isinstance, imap(c_type, (left_exp(_exp, None), right_exp(_exp, None)), repeat(None)), repeat(PointerType)
    ))


def addition_expression(_exp):
    assert not is_binary_pointer_expression(_exp)  # we are not allowed to add pointers ...
    return _exp


def subtraction_expression(_exp):
    if is_binary_pointer_expression(_exp):  # if subtracting two pointers, then the return type is a LongType
        return BinaryExpression(
            left_exp(_exp), oper(_exp), right_exp(_exp),
            LongType(LongType(location=loc(_exp)), unsigned=True, location=loc(_exp)),
            location=loc(_exp)
        )
    return _exp


default_additive_expression_rules = {
    TOKENS.PLUS: addition_expression,
    TOKENS.MINUS: subtraction_expression
}


def additive_expression(tokens, symbol_table, rules=default_additive_expression_rules):
    # : multiplicative_expression ('+' multiplicative_expression | '-' multiplicative_expression)*
    exp = multiplicative_expression(tokens, symbol_table)
    while peek(tokens, '') in rules:
        exp = rules[peek(tokens, '')](
            get_binary_expression(tokens, symbol_table, exp, multiplicative_expression, NumericType)
        )
    return exp
additive_expression.rules = default_additive_expression_rules


def shift_expression(tokens, symbol_table):  # : additive_expression (('<<'|'>>') additive_expression)*
    exp = additive_expression(tokens, symbol_table)
    while peek(tokens, '') in rules(shift_expression):
        exp = get_binary_expression(tokens, symbol_table, exp, additive_expression, IntegralType)
    return exp
shift_expression.rules = {TOKENS.SHIFT_LEFT, TOKENS.SHIFT_RIGHT}


def relational_expression(tokens, symbol_table):
    # : shift_expression (('<'|'>'|'<='|'>=') shift_expression)*
    exp = shift_expression(tokens, symbol_table)
    while peek(tokens, '') in rules(relational_expression):
        exp = get_binary_expression(tokens, symbol_table, exp, shift_expression, NumericType)
    return exp
relational_expression.rules = {
    TOKENS.LESS_THAN, TOKENS.GREATER_THAN, TOKENS.LESS_THAN_OR_EQUAL, TOKENS.GREATER_THAN_OR_EQUAL
}


def equality_expression(tokens, symbol_table):
    # : relational_expression (('=='|'!=') relational_expression)*
    exp = relational_expression(tokens, symbol_table)
    while peek(tokens, '') in rules(equality_expression):
        exp = get_binary_expression(tokens, symbol_table, exp, relational_expression, NumericType)
    return exp
equality_expression.rules = {TOKENS.EQUAL_EQUAL, TOKENS.NOT_EQUAL}


def and_expression(tokens, symbol_table):
    # : equality_expression ('&' equality_expression)*
    exp = equality_expression(tokens, symbol_table)
    while peek(tokens, '') in rules(and_expression):
        exp = get_binary_expression(tokens, symbol_table, exp, equality_expression, IntegralType)
    return exp
and_expression.rules = {TOKENS.AMPERSAND}


def exclusive_or_expression(tokens, symbol_table):
    # : and_expression ('^' and_expression)*
    exp = and_expression(tokens, symbol_table)
    while peek(tokens, '') in rules(exclusive_or_expression):
        exp = get_binary_expression(tokens, symbol_table, exp, and_expression, IntegralType)
    return exp
exclusive_or_expression.rules = {TOKENS.CARET}


def inclusive_or_expression(tokens, symbol_table):
    # : exclusive_or_expression ('|' exclusive_or_expression)*
    exp = exclusive_or_expression(tokens, symbol_table)
    while peek(tokens, '') == TOKENS.BAR:
        exp = get_binary_expression(tokens, symbol_table, exp, exclusive_or_expression, IntegralType)
    return exp


def logical_and_expression(tokens, symbol_table):
    # : inclusive_or_expression ('&&' inclusive_or_expression)*
    exp = inclusive_or_expression(tokens, symbol_table)
    while peek(tokens, '') == TOKENS.LOGICAL_AND:
        exp = get_binary_expression(tokens, symbol_table, exp, inclusive_or_expression, NumericType)
    return exp


def logical_or_expression(tokens, symbol_table):
    # : logical_and_expression ('||' logical_and_expression)*
    exp = logical_and_expression(tokens, symbol_table)
    while peek(tokens, '') == TOKENS.LOGICAL_OR:
        exp = get_binary_expression(tokens, symbol_table, exp, logical_and_expression, NumericType)
    return exp


@reduce_expression
def conditional_expression(tokens, symbol_table):
    # logical_or_expression ('?' expression ':' conditional_expression)?
    exp = logical_or_expression(tokens, symbol_table)
    if peek(tokens, '') in rules(conditional_expression):
        location = loc(error_if_not_value(tokens, TOKENS.QUESTION))
        _ = error_if_not_type(c_type(exp), NumericType)
        if_exp_is_true = assignment_expression(tokens, symbol_table)
        _ = error_if_not_value(tokens, TOKENS.COLON)
        if_exp_is_false = conditional_expression(tokens, symbol_table)

        ctype_1, ctype_2 = imap(c_type, (if_exp_is_true, if_exp_is_false))
        if safe_type_coercion(ctype_1, ctype_2):
            ctype = ctype_1(location)
        elif safe_type_coercion(ctype_2, ctype_1):
            ctype = ctype_2(location)
        else:
            raise ValueError('{l} Could not determine type for ternary-expr, giving the types {t1} and {t2}'.format(
                t1=ctype_1, t2=ctype_2
            ))
        return TernaryExpression(exp, if_exp_is_true, if_exp_is_false, ctype, location)
    return exp
conditional_expression.rules = {TOKENS.QUESTION}


def numeric_type(tokens, symbol_table, l_exp):
    exp = get_binary_expression(tokens, symbol_table, l_exp, assignment_expression, NumericType)
    return CompoundAssignmentExpression(left_exp(exp), oper(exp), right_exp(exp), c_type(l_exp)(loc(exp)), loc(exp))


def integral_type(tokens, symbol_table, l_exp):
    exp = get_binary_expression(tokens, symbol_table, l_exp, assignment_expression, IntegralType)
    return CompoundAssignmentExpression(left_exp(exp), oper(exp), right_exp(exp), c_type(l_exp)(loc(exp)), loc(exp))


def assign(tokens, symbol_table, l_exp):
    operator, r_exp = consume(tokens), assignment_expression(tokens, symbol_table)
    return AssignmentExpression(l_exp, operator, r_exp, c_type(l_exp)(loc(oper)), loc(operator))


def assignment_expression(tokens, symbol_table):
    # : conditional_expression | conditional_expression assignment_operator assignment_expression
    left_value_exp = conditional_expression(tokens, symbol_table)
    return rules(assignment_expression)[peek(tokens)](tokens, symbol_table, left_value_exp) \
        if peek(tokens, '') in rules(assignment_expression) else left_value_exp

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