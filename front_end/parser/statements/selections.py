__author__ = 'samyvilar'

from collections import defaultdict

from sequences import peek, consume
from front_end.loader.locations import loc, EOFLocation
from front_end.tokenizer.tokens import TOKENS

from front_end.parser.ast.statements import IfStatement, ElseStatement, SwitchStatement
from front_end.parser.expressions.expression import expression

from front_end.errors import error_if_not_value


def no_rule(tokens, *_):
    raise ValueError('{l} selection_statement expected either "if" or "switch: got {got}'.format(
        l=loc(peek(tokens, default=EOFLocation)), got=peek(tokens, default=''),
    ))


def _if(tokens, symbol_table, statement):
    location = loc(consume(tokens))
    _ = error_if_not_value(tokens, TOKENS.LEFT_PARENTHESIS)
    exp = expression(tokens, symbol_table)
    _ = error_if_not_value(tokens, TOKENS.RIGHT_PARENTHESIS)

    yield IfStatement(exp, statement(tokens, symbol_table, statement), location)
    if peek(tokens, default='') == TOKENS.ELSE:
        location = loc(consume(tokens))
        yield ElseStatement(statement(tokens, symbol_table, statement), location)


def switch(tokens, symbol_table, statement):
    location = loc(consume(tokens))
    _ = error_if_not_value(tokens, TOKENS.LEFT_PARENTHESIS)
    exp = expression(tokens, symbol_table)
    _ = error_if_not_value(tokens, TOKENS.RIGHT_PARENTHESIS)
    yield SwitchStatement(exp, statement(tokens, symbol_table, statement), location)


def selection_statement(tokens, symbol_table, statement):
    """
        : 'if' '(' expression ')' statement ('else' statement)?
        | 'switch' '(' expression ')' statement
    """
    return selection_statement.rules[peek(tokens, default='')](tokens, symbol_table, statement)
selection_statement.rules = defaultdict(lambda: no_rule)
selection_statement.rules.update({
    TOKENS.IF:_if,
    TOKENS.SWITCH:switch,
})