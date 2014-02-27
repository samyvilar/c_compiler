__author__ = 'samyvilar'

from utils.sequences import peek, consume, peek_or_terminal
from utils.rules import rules, set_rules
from front_end.loader.locations import loc, EOFLocation
from front_end.tokenizer.tokens import TOKENS, IDENTIFIER


from front_end.parser.ast.expressions import EmptyExpression
from front_end.parser.ast.statements import ContinueStatement, BreakStatement, ReturnStatement, GotoStatement

from front_end.parser.types import VoidType, safe_type_coercion, c_type

from utils.errors import error_if_not_value, error_if_not_type


from loggers import logging


logger = logging.getLogger('parser')


def _continue(tokens, symbol_table):
    location = loc(consume(tokens))
    return ContinueStatement(location)


def _break(tokens, symbol_table):
    location = loc(consume(tokens))
    return BreakStatement(location)


def _return(tokens, symbol_table):
    location = loc(consume(tokens))
    ret_type = symbol_table['__ RETURN_TYPE __']

    ret_exp = EmptyExpression(VoidType(location), location)
    if peek_or_terminal(tokens) != TOKENS.SEMICOLON:
        ret_exp = symbol_table['__ expression __'](tokens, symbol_table)

    if not isinstance(ret_exp, EmptyExpression) and isinstance(ret_type, VoidType):
        raise ValueError('{l} void-function returning a value ...'.format(l=loc(ret_exp)))

    if not safe_type_coercion(c_type(ret_exp), ret_type):
        raise ValueError('{l} Unable to coerce from {f} to {t}'.format(l=loc(ret_exp), f=c_type(ret_exp), t=ret_type))

    return ReturnStatement(ret_exp, location)


def _goto(tokens, symbol_table):
    location = loc(consume(tokens))
    return GotoStatement(error_if_not_type(consume(tokens, EOFLocation), IDENTIFIER), location)


def jump_statement(tokens, symbol_table):
    """
        : 'goto' IDENTIFIER ';'
        | 'continue' ';'
        | 'break' ';'
        | 'return' ';'
        | 'return' expression ';'
    """
    stmnt = rules(jump_statement)[peek(tokens)](tokens, symbol_table)
    _ = error_if_not_value(tokens, TOKENS.SEMICOLON)
    yield stmnt
set_rules(
    jump_statement,
    ((TOKENS.GOTO, _goto), (TOKENS.CONTINUE, _continue), (TOKENS.BREAK, _break), (TOKENS.RETURN, _return)),
)