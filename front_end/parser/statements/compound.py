__author__ = 'samyvilar'

from collections import defaultdict
from itertools import chain, izip, repeat

from sequences import peek, consume
from logging_config import logging

from front_end.loader.locations import loc, EOFLocation
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
        l=loc(peek(tokens, EOFLocation)), t=peek(tokens, '')
    ))


def _empty_statement(tokens, *_):
    yield EmptyStatement(loc(error_if_not_value(tokens, TOKENS.SEMICOLON)))


def _expression(expr):
    yield expr


def compound_statement(tokens, symbol_table, statement_func):  #: '{' statement*  '}'
    _ = error_if_not_value(tokens, TOKENS.LEFT_BRACE)
    symbol_table = push(symbol_table)
    while peek(tokens) != TOKENS.RIGHT_BRACE:
        yield statement_func(tokens, symbol_table, statement_func)
    _, _ = error_if_not_value(tokens, TOKENS.RIGHT_BRACE), pop(symbol_table)


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

    if isinstance(peek(tokens, ''), IDENTIFIER):
        label_name = consume(tokens)
        if peek(tokens, '') == TOKENS.COLON:
            _ = consume(tokens)
            return label_stmnt(label_name, statement_func(tokens, symbol_table, statement_func))
        # it must be an expression, TODO: figure out a way without using dangerous chain!
        tokens = chain((label_name, consume(tokens)), tokens)
        expr = expression(tokens, symbol_table)
        _ = error_if_not_value(tokens, TOKENS.SEMICOLON)
        return _expression(expr)

    if peek(tokens, '') in statement.rules:
        return statement.rules[peek(tokens)](tokens, symbol_table, statement_func)

    if peek(tokens, ''):
        expr = expression(tokens, symbol_table)
        _ = error_if_not_value(tokens, TOKENS.SEMICOLON)
        return _expression(expr)

    raise ValueError('{l} No rule could be found to create statement, got {got}'.format(
        l=loc(peek(tokens, EOFLocation)), got=peek(tokens, '')
    ))
statement.rules = defaultdict(lambda: no_rule)
statement.rules.update(chain(
    izip(labeled_statement.rules, repeat(labeled_statement)),
    izip(selection_statement.rules, repeat(selection_statement)),
    izip(iteration_statement.rules, repeat(iteration_statement)),
    izip(jump_statement.rules, repeat(jump_statement)),
    (
        (TOKENS.LEFT_BRACE, _comp_stmnt),
        (TOKENS.SEMICOLON, _empty_statement),
    )
))