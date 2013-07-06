__author__ = 'samyvilar'

from collections import defaultdict

from sequences import peek, consume
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

from front_end.errors import error_if_not_value, error_if_empty


# Primary expression found at the heart of all expressions.
def primary_expression(tokens, symbol_table):   #: IDENTIFIER | constant | '(' expression ')'
    if isinstance(peek(tokens, default=''), IDENTIFIER):
        identifier = consume(tokens)
        return IdentifierExpression(identifier, c_type(symbol_table[identifier]), loc(identifier))
    if isinstance(peek(tokens, default=''), CONSTANT):
        rules = {
            CHAR: lambda token: ConstantExpression(ord(token), CharType(loc(token)), loc(token)),
            STRING: lambda token: ConstantExpression(token, StringType(len(token), loc(token)), loc(token)),
            INTEGER: lambda token: ConstantExpression(int(token), IntegerType(loc(token)), loc(token)),
            FLOAT: lambda token: ConstantExpression(float(token), DoubleType(loc(token)), loc(token)),
        }
        return rules[type(peek(tokens))](consume(tokens))
    if peek(tokens, default='') == TOKENS.LEFT_PARENTHESIS:
        _ = consume(tokens)
        exp = expression(tokens, symbol_table)
        _ = error_if_not_value(tokens, TOKENS.RIGHT_PARENTHESIS)
        return exp

    raise ValueError('{l} Could not parse primary_expression, expected IDENTIFIER, CONSTANT, ( got {token}'.format(
        l=loc(peek(tokens, default='')), token=peek(tokens, default='')
    ))


def postfix_expression(tokens, symbol_table, primary_exp=None):
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
    if primary_exp is None:
        primary_exp = primary_expression(tokens, symbol_table)

    # noinspection PyUnresolvedReferences
    while peek(tokens, default='') in postfix_expression.rules:
        primary_exp = postfix_expression.rules[peek(tokens)](tokens, symbol_table, primary_exp, expression)

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
    error_if_empty(tokens)
    # Check if postfix expression is possible.
    if isinstance(peek(tokens), (IDENTIFIER, CONSTANT)) or peek(tokens) == TOKENS.LEFT_PARENTHESIS:
        return postfix_expression(tokens, symbol_table)

    exp_func = cast_expression if peek(tokens, default='') in unary.unary_operator.rules else unary_expression
    # noinspection PyUnresolvedReferences
    return unary_expression.rules[peek(tokens)](tokens, symbol_table, exp_func)
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
    if peek(tokens, default='') == TOKENS.LEFT_PARENTHESIS:
        _ = consume(tokens)
        if isinstance(symbol_table.get(peek(tokens, default=''), ''), CType):
            obj = type_name(tokens, symbol_table)
            _ = error_if_not_value(tokens, TOKENS.RIGHT_PARENTHESIS)
            return CastExpression(cast_expression(tokens, symbol_table), obj, loc(obj))
        # unary_expression -> postfix_expression -> primary_expression (postfix_expression)*
        # This is the only way to deal with the ambiguity without modifying the token stream and
        # creating havoc ....
        prim_exp = expression(tokens, symbol_table)
        _ = error_if_not_value(tokens, TOKENS.RIGHT_PARENTHESIS)
        return postfix_expression(tokens, symbol_table, primary_exp=prim_exp)
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