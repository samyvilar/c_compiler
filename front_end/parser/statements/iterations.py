__author__ = 'samyvilar'

from utils.sequences import peek, peek_or_terminal
from utils.rules import rules, set_rules
from front_end.loader.locations import loc, EOFLocation
from front_end.tokenizer.tokens import TOKENS

from front_end.parser.ast.statements import ForStatement, WhileStatement, DoWhileStatement
from front_end.parser.ast.expressions import EmptyExpression, TrueExpression

from front_end.parser.types import VoidType

from utils.errors import error_if_not_value


def no_rule(tokens, *_):
    raise ValueError('{l} expected either TOKENS.FOR, TOKENS.WHILE, or TOKENS.DO got {got}'.format(
        l=loc(peek(tokens, EOFLocation)), got=peek(tokens, '')
    ))


def for_stmnt(tokens, symbol_table):
    location, _ = loc(error_if_not_value(tokens, TOKENS.FOR)), error_if_not_value(tokens, TOKENS.LEFT_PARENTHESIS)
    statement, expression = symbol_table['__ statement __'], symbol_table['__ expression __']

    init_exp = EmptyExpression(VoidType(location), location)
    if peek_or_terminal(tokens) != TOKENS.SEMICOLON:
        init_exp = expression(tokens, symbol_table)
    _ = error_if_not_value(tokens, TOKENS.SEMICOLON)

    conditional_exp = TrueExpression(location)
    if peek_or_terminal(tokens) != TOKENS.SEMICOLON:
        conditional_exp = expression(tokens, symbol_table)
    _ = error_if_not_value(tokens, TOKENS.SEMICOLON)

    update_exp = EmptyExpression(VoidType(location), location)
    if peek_or_terminal(tokens) != TOKENS.RIGHT_PARENTHESIS:
        update_exp = expression(tokens, symbol_table)
    _ = error_if_not_value(tokens, TOKENS.RIGHT_PARENTHESIS)

    yield ForStatement(init_exp, conditional_exp, update_exp, statement(tokens, symbol_table), location)


def do_while_stmnt(tokens, symbol_table):
    location = loc(error_if_not_value(tokens, TOKENS.DO))

    def exp(tokens, symbol_table):
        expression = symbol_table['__ expression __']
        _, _ = error_if_not_value(tokens, TOKENS.WHILE), error_if_not_value(tokens, TOKENS.LEFT_PARENTHESIS)
        expr = expression(tokens, symbol_table)
        _, _ = error_if_not_value(tokens, TOKENS.RIGHT_PARENTHESIS), error_if_not_value(tokens, TOKENS.SEMICOLON)
        yield expr

    yield DoWhileStatement(exp(tokens, symbol_table), symbol_table['__ statement __'](tokens, symbol_table), location)


def while_stmnt(tokens, symbol_table):
    location = loc(error_if_not_value(tokens, TOKENS.WHILE))
    _ = error_if_not_value(tokens, TOKENS.LEFT_PARENTHESIS)
    exp = symbol_table['__ expression __'](tokens, symbol_table)
    _ = error_if_not_value(tokens, TOKENS.RIGHT_PARENTHESIS)

    yield WhileStatement(exp, symbol_table['__ statement __'](tokens, symbol_table), location)


def iteration_statement(tokens, symbol_table):
    """
        : 'while' '(' expression ')' statement
        | 'do' statement 'while' '(' expression ')' ';'
        | 'for' '(' expression?; expression?; expression? ')' statement
    """
    return rules(iteration_statement)[peek(tokens, '')](tokens, symbol_table)
set_rules(iteration_statement, ((TOKENS.WHILE, while_stmnt), (TOKENS.DO, do_while_stmnt), (TOKENS.FOR, for_stmnt)))