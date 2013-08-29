__author__ = 'samyvilar'

from collections import defaultdict

from sequences import peek, consume
from front_end.loader.locations import loc, EOFLocation
from front_end.tokenizer.tokens import TOKENS, IDENTIFIER


from front_end.parser.ast.expressions import EmptyExpression
from front_end.parser.ast.statements import ContinueStatement, BreakStatement, ReturnStatement, GotoStatement

from front_end.parser.types import VoidType, safe_type_coercion, c_type

from front_end.parser.expressions.expression import expression
from front_end.errors import error_if_not_value, error_if_not_type


from logging_config import logging


logger = logging.getLogger('parser')


def no_rule(tokens, *_):
    raise ValueError('{l} jump_statement was expecting one of "goto", "continue", "break", "return" got {got}'.format(
        l=loc(peek(tokens, EOFLocation)), got=peek(tokens, '')
    ))


def _continue(tokens, symbol_table, statement_func):
    location = loc(consume(tokens))
    return ContinueStatement(location)


def _break(tokens, symbol_table, statement_func):
    location = loc(consume(tokens))
    return BreakStatement(location)


def _return(tokens, symbol_table, statement_func):
    location = loc(consume(tokens))
    ret_type = symbol_table['__ RETURN_TYPE __']

    ret_exp = EmptyExpression(VoidType(location), location)
    if peek(tokens, '') != TOKENS.SEMICOLON:
        ret_exp = expression(tokens, symbol_table)

    if ret_exp and isinstance(ret_type, VoidType):
        raise ValueError('{l} void-function returning a value ...'.format(l=loc(ret_exp)))

    if not safe_type_coercion(c_type(ret_exp), ret_type):
        raise ValueError('{l} Unable to coerce from {f} to {t}'.format(l=loc(ret_exp), f=c_type(ret_exp), t=ret_type))

    return ReturnStatement(ret_exp, location)


def _goto(tokens, symbol_table, statement_func):
    location = loc(consume(tokens))
    return GotoStatement(error_if_not_type(consume(tokens, EOFLocation), IDENTIFIER), location)


def jump_statement(tokens, symbol_table, statement_func):
    """
        : 'goto' IDENTIFIER ';'
        | 'continue' ';'
        | 'break' ';'
        | 'return' ';'
        | 'return' expression ';'
    """
    yield jump_statement.rules[peek(tokens)](tokens, symbol_table, statement_func)
    _ = error_if_not_value(tokens, TOKENS.SEMICOLON)
jump_statement.rules = defaultdict(lambda: no_rule)
jump_statement.rules.update({
    TOKENS.GOTO: _goto,
    TOKENS.CONTINUE: _continue,
    TOKENS.BREAK: _break,
    TOKENS.RETURN: _return,
})