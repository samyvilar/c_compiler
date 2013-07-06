__author__ = 'samyvilar'

from collections import defaultdict

from sequences import peek, consume
from front_end.loader.locations import loc
from front_end.tokenizer.tokens import TOKENS, IDENTIFIER


from front_end.parser.ast.expressions import EmptyExpression
from front_end.parser.ast.statements import ContinueStatement, BreakStatement, ReturnStatement, GotoStatement

from front_end.parser.types import VoidType

from front_end.parser.expressions.expression import expression
from front_end.errors import error_if_not_value, error_if_not_type


def no_rule(tokens, *_):
    raise ValueError('{l} jump_statement was expecting one of "goto", "continue", "break", "return" got {got}'.format(
        l=loc(peek(tokens, default='')) or '__EOF__', got=peek(tokens, default='')
    ))


def _continue(tokens, symbol_table, statement_func):
    location = loc(consume(tokens))
    return ContinueStatement(location)


def _break(tokens, symbol_table, statement_func):
    location = loc(consume(tokens))
    return BreakStatement(location)


def _return(tokens, symbol_table, statement_func):
    location = loc(consume(tokens))

    ret_exp = EmptyExpression(VoidType(location), location)
    if peek(tokens, default='') != TOKENS.SEMICOLON:
        ret_exp = expression(tokens, symbol_table)

    return ReturnStatement(ret_exp, location)


def _goto(tokens, symbol_table, statement_func):
    location = loc(consume(tokens))
    return GotoStatement(error_if_not_type(tokens, IDENTIFIER), location)


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