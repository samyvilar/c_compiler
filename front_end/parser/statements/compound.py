__author__ = 'samyvilar'

from collections import defaultdict

from logging_config import logging

from front_end.loader.locations import loc
from front_end.tokenizer.tokens import TOKENS, IDENTIFIER
from front_end.parser.symbol_table import SymbolTable

from front_end.parser.ast.statements import EmptyStatement, CompoundStatement, no_effect
from front_end.parser.ast.statements import CaseStatement, ContinueStatement, BreakStatement, DefaultStatement

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
        l=loc(tokens[0]), t=tokens[0]
    ))


def _empty_statement(tokens, *_):
    return EmptyStatement(loc(tokens.pop(0)))


def _expression(tokens, symbol_table, *_):
    exp = expression(tokens, symbol_table)
    _ = error_if_not_value(tokens, TOKENS.SEMICOLON)
    return exp


def compound_statement(tokens, symbol_table, statement_func, disallowed_statements):  #: '{' statement*  '}'
    location = loc(error_if_not_value(tokens, TOKENS.LEFT_BRACE))

    symbol_table.push_name_space()
    statements = []
    while tokens and tokens[0] != TOKENS.RIGHT_BRACE:
        # declarations returns a list of declarations.
        stmnt = statement_func(tokens, symbol_table, statement_func, disallowed_statements)
        if no_effect(stmnt):
            logger.warning('{l} Statement {t} removed, empty or no effect.'.format(l=loc(stmnt), t=stmnt))
        elif type(stmnt) in disallowed_statements:
            raise ValueError('{l} Statement {t} is not allowed withing this context'.format(l=loc(stmnt), t=stmnt))
        else:
            statements.append(stmnt)
    _ = error_if_not_value(tokens, TOKENS.RIGHT_BRACE)
    symbol_table.pop_name_space()

    return CompoundStatement(statements, location)


def statement(
        tokens,
        symbol_table=None,
        statement_func=None,
        disallowed_statements=(CaseStatement, DefaultStatement, BreakStatement, ContinueStatement)
):
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

    if len(tokens) > 1 and isinstance(tokens[0], IDENTIFIER) and tokens[1] == TOKENS.COLON:
        return labeled_statement(tokens, symbol_table, statement_func, disallowed_statements)

    if tokens and tokens[0] in statement.rules:
        return statement.rules[tokens[0]](tokens, symbol_table, statement_func, disallowed_statements)

    if tokens:
        return _expression(tokens, symbol_table)

    raise ValueError('{l} No rule could be found to create statement.'.format(l=loc(tokens)))

statement.rules = defaultdict(lambda: no_rule)
statement.rules.update({
    TOKENS.LEFT_BRACE: compound_statement,
    TOKENS.SEMICOLON: _empty_statement,
})
statement.rules.update({rule: labeled_statement for rule in labeled_statement.rules})
statement.rules.update({rule: selection_statement for rule in selection_statement.rules})
statement.rules.update({rule: iteration_statement for rule in iteration_statement.rules})
statement.rules.update({rule: jump_statement for rule in jump_statement.rules})