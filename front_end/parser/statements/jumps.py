__author__ = 'samyvilar'

from collections import defaultdict

from front_end.loader.locations import loc
from front_end.tokenizer.tokens import TOKENS, IDENTIFIER

from front_end.parser.ast.declarations import name
from front_end.parser.ast.expressions import EmptyExpression
from front_end.parser.ast.statements import ContinueStatement, BreakStatement, ReturnStatement, GotoStatement

from front_end.parser.types import VoidType

from front_end.parser.expressions.expression import expression
from front_end.errors import error_if_not_value, error_if_not_type


def no_rule(tokens, *_):
    raise ValueError('{l} jump_statement was expecting one of "goto", "continue", "break", "return" got {got}'.format(
        l=loc(tokens[0]), got=tokens[0]
    ))


def _continue(tokens, symbol_table, statement_func, disallowed_statements):
    location = loc(tokens.pop(0))
    if ContinueStatement in disallowed_statements:
        raise ValueError('{l} continue statement is not allowed in this context'.format(l=location))
    return ContinueStatement(location)


def _break(tokens, symbol_table, statement_func, disallowed_statements):
    location = loc(tokens.pop(0))
    if BreakStatement in disallowed_statements:
        raise ValueError('{l} break statement is not allowed in this context'.format(l=location))
    return BreakStatement(location)


def _return(tokens, symbol_table, statement_func, disallowed_statements):
    location = loc(tokens.pop(0))

    ret_exp = EmptyExpression(VoidType(location), location)
    if tokens and tokens[0] != TOKENS.SEMICOLON:
        ret_exp = expression(tokens, symbol_table)

    stmnt = ReturnStatement(ret_exp, location)
    symbol_table[stmnt] = stmnt
    return stmnt


def _goto(tokens, symbol_table, statement_func, disallowed_statements):
    location = loc(tokens.pop(0))
    stmnt = GotoStatement(error_if_not_type(tokens, IDENTIFIER), location)
    symbol_table[stmnt] = stmnt
    return stmnt


def jump_statement(tokens, symbol_table, statement_func, disallowed_statements):
    """
        : 'goto' IDENTIFIER ';'
        | 'continue' ';'
        | 'break' ';'
        | 'return' ';'
        | 'return' expression ';'
    """
    stmnt = jump_statement.rules[tokens[0]](tokens, symbol_table, statement_func, disallowed_statements)
    _ = error_if_not_value(tokens, TOKENS.SEMICOLON)
    return stmnt
jump_statement.rules = defaultdict(lambda: no_rule)
jump_statement.rules.update({
    TOKENS.GOTO: _goto,
    TOKENS.CONTINUE: _continue,
    TOKENS.BREAK: _break,
    TOKENS.RETURN: _return,
})