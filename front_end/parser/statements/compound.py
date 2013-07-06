__author__ = 'samyvilar'

from collections import defaultdict
from itertools import chain

from sequences import peek, consume
from logging_config import logging

from front_end.loader.locations import loc
from front_end.tokenizer.tokens import TOKENS, IDENTIFIER
from front_end.parser.symbol_table import SymbolTable, push, pop

from front_end.parser.ast.statements import EmptyStatement, CompoundStatement, LabelStatement

from front_end.parser.declarations.declarations import declaration, is_declaration
from front_end.parser.expressions.expression import expression
from front_end.parser.statements.labels import labeled_statement
from front_end.parser.statements.selections import selection_statement
from front_end.parser.statements.iterations import iteration_statement
from front_end.parser.statements.jumps import jump_statement

from front_end.errors import error_if_not_value


logger = logging.getLogger('parser')


def no_rule(tokens, *_):
    raise ValueError('{l} Could not locate a rule for statement starting with {t}.'.format(
        l=loc(peek(tokens, default='')) or '__EOF__', t=peek(tokens, default='')
    ))


def _empty_statement(tokens, *_):
    yield EmptyStatement(loc(error_if_not_value(tokens, TOKENS.SEMICOLON)))


def _expression(expr):
    yield expr


def compound_statement(tokens, symbol_table, statement_func):  #: '{' statement*  '}'
    _ = error_if_not_value(tokens, TOKENS.LEFT_BRACE)
    symbol_table = push(symbol_table)
    while peek(tokens, default='') != TOKENS.RIGHT_BRACE:
        yield statement_func(tokens, symbol_table, statement_func)
    _ = error_if_not_value(tokens, TOKENS.RIGHT_BRACE)
    _ = pop(symbol_table)


def label_stmnt(label_name, stmnt):
    yield LabelStatement(label_name, stmnt, loc(label_name))


def _comp_stmnt(tokens, symbol_table, statement_func):
    yield CompoundStatement(compound_statement(tokens, symbol_table, statement_func), loc(peek(tokens)))


def statement(tokens, symbol_table=None, statement_func=None):
    """
        : declaration
        | labeled_statement
        | compound_statement
        | selection_statement
        | iteration_statement
        | jump_statement
        | expression_statement
        | expression ';'
        | ;
    """
    symbol_table = symbol_table or SymbolTable()
    statement_func = statement_func or statement

    if is_declaration(tokens, symbol_table):
        return declaration(tokens, symbol_table)

    if isinstance(peek(tokens, default=''), IDENTIFIER):
        label_name = consume(tokens)
        if peek(tokens, default='') == TOKENS.COLON:
            _ = consume(tokens)
            return label_stmnt(label_name, statement_func(tokens, symbol_table, statement_func))
        # it must be an expression, TODO: figure out a way without using dangerous chain!
        tokens = chain((label_name, consume(tokens)), tokens)
        expr = expression(tokens, symbol_table)
        _ = error_if_not_value(tokens, TOKENS.SEMICOLON)
        return _expression(expr)

    if peek(tokens, default='') in statement.rules:
        return statement.rules[peek(tokens)](tokens, symbol_table, statement_func)

    if peek(tokens, default=False):
        expr = expression(tokens, symbol_table)
        _ = error_if_not_value(tokens, TOKENS.SEMICOLON)
        return _expression(expr)

    raise ValueError('{l} No rule could be found to create statement, got {got}'.format(
        l=loc(peek(tokens, default='')) or '__EOF__', got=peek(tokens, default='')
    ))
statement.rules = defaultdict(lambda: no_rule)
statement.rules.update({
    TOKENS.LEFT_BRACE: _comp_stmnt,
    TOKENS.SEMICOLON: _empty_statement,
})
statement.rules.update({rule: labeled_statement for rule in labeled_statement.rules})
statement.rules.update({rule: selection_statement for rule in selection_statement.rules})
statement.rules.update({rule: iteration_statement for rule in iteration_statement.rules})
statement.rules.update({rule: jump_statement for rule in jump_statement.rules})