__author__ = 'samyvilar'

from itertools import chain, imap

from utils.sequences import peek, consume, peek_or_terminal
from utils.rules import rules, set_rules
from front_end.loader.locations import loc, EOFLocation
from front_end.tokenizer.tokens import TOKENS

from utils.symbol_table import push, pop, SymbolTable
from front_end.parser.ast.statements import IfStatement, ElseStatement, SwitchStatement, EmptyStatement

from utils.errors import error_if_not_value


def no_rule(tokens, *_):
    raise ValueError('{l} selection_statement expected either TOKENS.IF or TOKENS.SWITCH: got {got}'.format(
        l=loc(peek(tokens, EOFLocation)), got=peek(tokens, ''),
    ))


def _empty():
    yield EmptyStatement()


def else_statement(tokens, symbol_table):
    location, stmnt = '', _empty()
    if peek_or_terminal(tokens) == TOKENS.ELSE:
        location = loc(consume(tokens))
        stmnt = symbol_table['__ statement __'](tokens, symbol_table)
    yield ElseStatement(stmnt, location)


def _if(tokens, symbol_table):
    location, _ = loc(consume(tokens)), error_if_not_value(tokens, TOKENS.LEFT_PARENTHESIS)
    expression, statement = imap(symbol_table.__getitem__, ('__ expression __', '__ statement __'))
    expr, _ = expression(tokens, symbol_table), error_if_not_value(tokens, TOKENS.RIGHT_PARENTHESIS)
    yield IfStatement(expr, statement(tokens, symbol_table), else_statement(tokens, symbol_table), location)


def switch(tokens, symbol_table):
    def _pop_symbol_table(symbol_table):  # Pop symbol table once we have gone through the whole body ...
        _ = pop(symbol_table)
        yield EmptyStatement()
    expression, statement = imap(symbol_table.__getitem__, ('__ expression __', '__ statement __'))
    location, _ = loc(consume(tokens)), error_if_not_value(tokens, TOKENS.LEFT_PARENTHESIS)
    expr, _ = expression(tokens, symbol_table), error_if_not_value(tokens, TOKENS.RIGHT_PARENTHESIS)
    symbol_table = push(symbol_table)
    symbol_table['__ SWITCH STATEMENT __'] = SymbolTable()  # Add dict to track cases, emit error on duplicates.
    symbol_table['__ SWITCH EXPRESSION __'] = expr
    yield SwitchStatement(expr, chain(statement(tokens, symbol_table), _pop_symbol_table(symbol_table)), location)


def selection_statement(tokens, symbol_table):
    """
        : 'if' '(' expression ')' statement ('else' statement)?
        | 'switch' '(' expression ')' statement
    """
    return rules(selection_statement)[peek_or_terminal(tokens)](tokens, symbol_table)
set_rules(selection_statement, ((TOKENS.IF, _if), (TOKENS.SWITCH, switch)))