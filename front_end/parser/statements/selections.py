__author__ = 'samyvilar'

from itertools import chain
from collections import defaultdict

from sequences import peek, consume
from front_end.loader.locations import loc, EOFLocation, LocationNOTSET
from front_end.tokenizer.tokens import TOKENS

from front_end.parser.symbol_table import push, pop
from front_end.parser.ast.statements import IfStatement, ElseStatement, SwitchStatement, EmptyStatement
from front_end.parser.expressions.expression import expression

from front_end.errors import error_if_not_value


def no_rule(tokens, *_):
    raise ValueError('{l} selection_statement expected either "if" or "switch: got {got}'.format(
        l=loc(peek(tokens, EOFLocation)), got=peek(tokens, ''),
    ))


def _if(tokens, symbol_table, statement):
    location = loc(consume(tokens))
    _ = error_if_not_value(tokens, TOKENS.LEFT_PARENTHESIS)
    exp = expression(tokens, symbol_table)
    _ = error_if_not_value(tokens, TOKENS.RIGHT_PARENTHESIS)

    def else_statement(tokens, symbol_table, statement):
        def _empty():
            yield EmptyStatement('')
        if peek(tokens, '') == TOKENS.ELSE:
            location = loc(consume(tokens))
            stmnt = statement(tokens, symbol_table, statement)
        else:
            location = ''
            stmnt = _empty()
        yield ElseStatement(stmnt, location)

    yield IfStatement(
        exp,
        statement(tokens, symbol_table, statement),
        else_statement(tokens, symbol_table, statement),
        location
    )


def switch(tokens, symbol_table, statement):
    def _pop_symbol_table(symbol_table):  # Pop symbol table once we have gone through the whole body ...
        _ = pop(symbol_table)
        yield EmptyStatement()
    location, _ = loc(consume(tokens)), error_if_not_value(tokens, TOKENS.LEFT_PARENTHESIS)
    exp, _ = expression(tokens, symbol_table), error_if_not_value(tokens, TOKENS.RIGHT_PARENTHESIS)
    symbol_table = push(symbol_table)
    symbol_table['__ SWITCH STATEMENT __'] = {}  # Add dict to track cases, emit error on duplicates.
    yield SwitchStatement(
        exp,
        chain(statement(tokens, symbol_table, statement), _pop_symbol_table(symbol_table)),
        location
    )


def selection_statement(tokens, symbol_table, statement):
    """
        : 'if' '(' expression ')' statement ('else' statement)?
        | 'switch' '(' expression ')' statement
    """
    return selection_statement.rules[peek(tokens, '')](tokens, symbol_table, statement)
selection_statement.rules = defaultdict(lambda: no_rule)
selection_statement.rules.update({
    TOKENS.IF: _if,
    TOKENS.SWITCH: switch,
})