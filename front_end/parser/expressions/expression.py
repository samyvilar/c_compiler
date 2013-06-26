__author__ = 'samyvilar'

from collections import defaultdict

from front_end.loader.locations import loc
from front_end.tokenizer.tokens import TOKENS, IDENTIFIER, CONSTANT, CHAR, INTEGER, FLOAT, STRING

from front_end.parser.types import CType, CharType, StringType, IntegerType, DoubleType, c_type
from front_end.parser.ast.expressions import ConstantExpression, IdentifierExpression
from front_end.parser.ast.expressions import CastExpression

from front_end.parser.symbol_table import SymbolTable

import front_end.parser.expressions.postfix as postfix
import front_end.parser.expressions.unary as unary

from front_end.parser.expressions.binary import assignment_expression, logical_or_expression
from front_end.parser.declarations.declarators import type_name

from front_end.parser.expressions.reduce import reduce_expression

from front_end.errors import error_if_not_value


# Primary expression found at the heart of all expressions.
def primary_expression(tokens, symbol_table):   #: IDENTIFIER | constant | '(' expression ')'
    if tokens and isinstance(tokens[0], IDENTIFIER):
        identifier = tokens.pop(0)
        return IdentifierExpression(identifier, c_type(symbol_table[identifier]), loc(identifier))
    if tokens and isinstance(tokens[0], CONSTANT):
        rules = {
            CHAR: lambda token: ConstantExpression(ord(token), CharType(loc(token)), loc(token)),
            STRING: lambda token: ConstantExpression(token, StringType(len(token), loc(token)), loc(token)),
            INTEGER: lambda token: ConstantExpression(int(token), IntegerType(loc(token)), loc(token)),
            FLOAT: lambda token: ConstantExpression(float(token), DoubleType(loc(token)), loc(token)),
        }
        return rules[type(tokens[0])](tokens.pop(0))
    if tokens and tokens[0] == TOKENS.LEFT_PARENTHESIS:
        _ = tokens.pop(0)
        exp = expression(tokens, symbol_table)
        _ = error_if_not_value(tokens, TOKENS.RIGHT_PARENTHESIS)
        return exp

    raise ValueError('{l} Could not parse primary_expression, expected IDENTIFIER, CONSTANT, ( got {token}'.format(
        l=tokens and loc(tokens[0]) or loc(tokens), token=tokens and tokens[0]
    ))


def postfix_expression(tokens, symbol_table):
    """
    :   primary_expression
        (   '[' expression ']'
        |   '(' ')'
        |   '(' argument_expression_list ')'
        |   '.' IDENTIFIER
        |   '->' IDENTIFIER
        |   '++'
        |   '--'
        )*
    """
    primary_exp = primary_expression(tokens, symbol_table)

    # noinspection PyUnresolvedReferences
    while tokens and tokens[0] in postfix_expression.rules:
        primary_exp = postfix_expression.rules[tokens[0]](tokens, symbol_table, primary_exp, expression)

    return primary_exp

postfix_expression.rules = {
    TOKENS.LEFT_BRACKET: postfix.subscript_oper,
    TOKENS.LEFT_PARENTHESIS: postfix.function_call,
    TOKENS.DOT: postfix.dot_oper,
    TOKENS.ARROW: postfix.arrow_operator,
    TOKENS.PLUS_PLUS: postfix.inc_dec,
    TOKENS.MINUS_MINUS: postfix.inc_dec,
}


@reduce_expression
def unary_expression(tokens, symbol_table):
    """
        : postfix_expression
        | '++' unary_expression
        | '--' unary_expression
        | unary_operator cast_expression
        | 'sizeof' '(' type_name |  unary_expression ')'
    """
    if not tokens:
        raise ValueError('{l} Expected postfix_expression, ++, --, unary_operator, sizeof, got {got}'.format(
            l=loc(tokens), got=tokens
        ))
    # Check if postfix expression is possible.
    if isinstance(tokens[0], (IDENTIFIER, CONSTANT)) or tokens[0] == TOKENS.LEFT_PARENTHESIS:
        return postfix_expression(tokens, symbol_table)
    exp_func = unary_expression
    # noinspection PyUnresolvedReferences
    if tokens[0] in unary.unary_operator.rules:  # unary_operators are followed by a cast expr
        exp_func = cast_expression

    # noinspection PyUnresolvedReferences
    return unary_expression.rules[tokens[0]](tokens, symbol_table, exp_func)
unary_expression.rules = defaultdict(lambda: unary.no_rule_found)
unary_expression.rules.update({
    TOKENS.PLUS_PLUS: unary.increment_decrement,
    TOKENS.MINUS_MINUS: unary.increment_decrement,
    TOKENS.SIZEOF: unary.size_of,
})
unary_expression.rules.update({rule: unary.unary_operator for rule in unary.unary_operator.rules})


@reduce_expression
def cast_expression(tokens, symbol_table):
    # : '(' type_name ')' cast_expression | unary_expression
    # There is a slight ambiguity here, both cast_expression and primary expression may begin with '('
    # but only cast expression maybe followed by type_name.
    if len(tokens) > 1 \
       and tokens[0] == TOKENS.LEFT_PARENTHESIS \
       and isinstance(symbol_table.get(tokens[1]), CType):
        location = loc(tokens.pop(0))
        obj = type_name(tokens, symbol_table)
        _ = error_if_not_value(tokens, TOKENS.RIGHT_PARENTHESIS)
        return CastExpression(cast_expression(tokens, symbol_table), obj, location)
    else:
        return unary_expression(tokens, symbol_table)


def expression(tokens, symbol_table=None):
    return assignment_expression(tokens, symbol_table or SymbolTable(), cast_expression)


def constant_expression(tokens, symbol_table):
    const_exp = logical_or_expression(tokens, symbol_table, cast_expression)
    if not isinstance(const_exp, ConstantExpression):
        raise ValueError('{l} Expected a constant expression got {got}'.format(
            l=loc(const_exp), got=const_exp
        ))
    return const_exp