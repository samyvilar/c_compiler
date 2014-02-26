__author__ = 'samyvilar'

from collections import defaultdict
from itertools import imap, repeat

from front_end.loader.locations import loc
from front_end.parser.types import c_type, logical_type
from front_end.tokenizer.tokens import TOKENS

from front_end.parser.ast.expressions import ConstantExpression, UnaryExpression, BinaryExpression, CastExpression
from front_end.parser.ast.expressions import EmptyExpression
from front_end.parser.types import IntegralType, FloatType, ArrayType

from front_end.parser.ast.expressions import left_exp, right_exp, oper, exp


def unary_exp(expr):
    # noinspection PyUnresolvedReferences
    return unary_exp.rules[oper(expr)](exp(expr)) if isinstance(exp(expr), ConstantExpression) else expr
unary_exp.rules = defaultdict(lambda: (lambda expr: expr))
unary_exp.rules.update({
    TOKENS.PLUS: lambda expr: ConstantExpression(exp(expr), c_type(expr)(loc(expr)), loc(expr)),
    TOKENS.MINUS: lambda expr: ConstantExpression(-1 * exp(expr), c_type(expr)(loc(expr)), loc(expr)),
    TOKENS.TILDE: lambda expr: ConstantExpression(~exp(expr), c_type(expr)(loc(expr)), loc(expr)),
    TOKENS.EXCLAMATION: lambda expr: ConstantExpression(int(bool(exp(expr))), logical_type(loc(expr)), loc(expr)),
})


def binary_exp(expr):
    if not all(imap(isinstance, (left_exp(expr), right_exp(expr)), repeat(ConstantExpression))):
        return expr

    exp_type = max(imap(c_type, (left_exp(expr), right_exp(expr))))(loc(expr))
    l_exp, r_exp, location = exp(left_exp(expr)), exp(right_exp(expr)), loc(expr)

    # noinspection PyUnresolvedReferences  '1 + 2 - 3 * 7 / 4'
    return binary_exp.rules[oper(expr)](
        expr=expr, left_exp=l_exp, right_exp=r_exp, location=location, exp_type=exp_type
    )
binary_exp.rules = defaultdict(lambda: (lambda **kwargs: kwargs['expr']))
binary_exp.rules.update({
    TOKENS.PLUS:
    lambda **kwargs: ConstantExpression(
        kwargs['left_exp'] + kwargs['right_exp'], kwargs['exp_type'], kwargs['location']),

    TOKENS.MINUS:
    lambda **kwargs: ConstantExpression(
        kwargs['left_exp'] - kwargs['right_exp'], kwargs['exp_type'], kwargs['location']),

    TOKENS.STAR:
    lambda **kwargs: ConstantExpression(
        kwargs['left_exp'] * kwargs['right_exp'], kwargs['exp_type'], kwargs['location']),

    TOKENS.FORWARD_SLASH:
    lambda **kwargs: ConstantExpression(
        kwargs['left_exp'] / kwargs['right_exp'], kwargs['exp_type'], kwargs['location']),

    TOKENS.PERCENTAGE:
    lambda **kwargs: ConstantExpression(
        kwargs['left_exp'] % kwargs['right_exp'], kwargs['exp_type'], kwargs['location']),

    TOKENS.SHIFT_LEFT:
    lambda **kwargs: ConstantExpression(
        kwargs['left_exp'] << kwargs['right_exp'], kwargs['exp_type'], kwargs['location']),

    TOKENS.SHIFT_RIGHT:
    lambda **kwargs: ConstantExpression(
        kwargs['left_exp'] >> kwargs['right_exp'], kwargs['exp_type'], kwargs['location']),

    TOKENS.AMPERSAND:
    lambda **kwargs: ConstantExpression(
        kwargs['left_exp'] & kwargs['right_exp'], kwargs['exp_type'], kwargs['location']),

    TOKENS.CARET:
    lambda **kwargs: ConstantExpression(
        kwargs['left_exp'] ^ kwargs['right_exp'], kwargs['exp_type'], kwargs['location']),

    TOKENS.BAR:
    lambda **kwargs: ConstantExpression(
        kwargs['left_exp'] | kwargs['right_exp'], kwargs['exp_type'], kwargs['location']),



    TOKENS.LOGICAL_AND:
    lambda **kwargs: ConstantExpression(
        int(bool(kwargs['left_exp'] and kwargs['right_exp'])), logical_type(kwargs['location']), kwargs['location']),

    TOKENS.LOGICAL_OR:
    lambda **kwargs: ConstantExpression(
        int(bool(kwargs['left_exp'] or kwargs['right_exp'])), logical_type(kwargs['location']), kwargs['location']),

    TOKENS.LESS_THAN:
    lambda **kwargs: ConstantExpression(
        kwargs['left_exp'] < kwargs['right_exp'], logical_type(kwargs['location']), kwargs['location']),

    TOKENS.GREATER_THAN:
    lambda **kwargs: ConstantExpression(
        int(kwargs['left_exp'] > kwargs['right_exp']), logical_type(kwargs['location']), kwargs['location']),

    TOKENS.LESS_THAN_OR_EQUAL:
    lambda **kwargs: ConstantExpression(
        int(kwargs['left_exp'] <= kwargs['right_exp']), logical_type(kwargs['location']), kwargs['location']),

    TOKENS.GREATER_THAN_OR_EQUAL:
    lambda **kwargs: ConstantExpression(
        int(kwargs['left_exp'] >= kwargs['right_exp']), logical_type(kwargs['location']), kwargs['location']),

    TOKENS.EQUAL_EQUAL:
    lambda **kwargs: ConstantExpression(
        int(kwargs['left_exp'] == kwargs['right_exp']), logical_type(kwargs['location']), kwargs['location']),

    TOKENS.NOT_EQUAL:
    lambda **kwargs: ConstantExpression(
        int(kwargs['left_exp'] != kwargs['right_exp']), logical_type(kwargs['location']), kwargs['location']),
})


def cast_exp(expr):
    if c_type(expr) == c_type(exp(expr)):
        return exp(expr)
    if isinstance(exp(expr), ConstantExpression) and not isinstance(c_type(exp(expr)), ArrayType):
        to_type = c_type(expr)
        expr = exp(expr)
        location = loc(expr)
        if isinstance(expr, EmptyExpression):
            return EmptyExpression(to_type, loc(expr))
        if isinstance(to_type, IntegralType):
            return ConstantExpression(int(exp(expr)), to_type(location), location)
        if isinstance(to_type, FloatType):
            return ConstantExpression(float(exp(expr)), to_type(location), location)
    return expr


def reduce_to_constant(expr):
    # noinspection PyUnresolvedReferences
    return reduce_to_constant.rules[type(expr)](expr)
reduce_to_constant.rules = defaultdict(lambda: (lambda expr: expr))
reduce_to_constant.rules.update({
    UnaryExpression: unary_exp,
    BinaryExpression: binary_exp,
    CastExpression: cast_exp,
})


def reduce_expression(func):
    def func_wrapper(*args):
        return reduce_to_constant(func(*args))
    return func_wrapper