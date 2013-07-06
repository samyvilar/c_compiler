__author__ = 'samyvilar'

from collections import defaultdict

from sequences import peek, consume
from front_end.loader.locations import loc
from front_end.tokenizer.tokens import TOKENS

from front_end.parser.ast.statements import ForStatement, WhileStatement, DoWhileStatement
from front_end.parser.ast.expressions import EmptyExpression, TrueExpression

from front_end.parser.types import VoidType

from front_end.parser.expressions.expression import expression
from front_end.errors import error_if_not_value


def no_rule(tokens, *_):
    raise ValueError('{l} expected either "for", "while", or "do" got {got}'.format(
        l=loc(peek(tokens, default='')) or '__EOF__', got=peek(tokens, default='')
    ))


def for_stmnt(tokens, symbol_table, statement_func):
    location, _ = loc(error_if_not_value(tokens, TOKENS.FOR)), error_if_not_value(tokens, TOKENS.LEFT_PARENTHESIS)

    init_exp = EmptyExpression(VoidType(location), location)
    if peek(tokens, default='') != TOKENS.SEMICOLON:
        init_exp = expression(tokens, symbol_table)
    _ = error_if_not_value(tokens, TOKENS.SEMICOLON)

    conditional_exp = TrueExpression(location)
    if peek(tokens, default='') != TOKENS.SEMICOLON:
        conditional_exp = expression(tokens, symbol_table)
    _ = error_if_not_value(tokens, TOKENS.SEMICOLON)

    update_exp = EmptyExpression(VoidType(location), location)
    if peek(tokens, default='') != TOKENS.RIGHT_PARENTHESIS:
        update_exp = expression(tokens, symbol_table)
    _ = error_if_not_value(tokens, TOKENS.RIGHT_PARENTHESIS)

    yield ForStatement(
        init_exp,
        conditional_exp,
        update_exp,
        statement_func(tokens, symbol_table, statement_func),
        location
    )


def do_while_stmnt(tokens, symbol_table, statement_func):
    location = loc(error_if_not_value(tokens, TOKENS.DO))

    def exp(tokens, symbol_table):
        _, _ = error_if_not_value(tokens, TOKENS.WHILE), error_if_not_value(tokens, TOKENS.LEFT_PARENTHESIS)
        expr = expression(tokens, symbol_table)
        _, _ = error_if_not_value(tokens, TOKENS.RIGHT_PARENTHESIS), error_if_not_value(tokens, TOKENS.SEMICOLON)
        yield expr

    yield DoWhileStatement(exp(tokens, symbol_table), statement_func(tokens, symbol_table, statement_func), location)


def while_stmnt(tokens, symbol_table, statement_func):
    location = loc(error_if_not_value(tokens, TOKENS.WHILE))
    _ = error_if_not_value(tokens, TOKENS.LEFT_PARENTHESIS)
    exp = expression(tokens, symbol_table)
    _ = error_if_not_value(tokens, TOKENS.RIGHT_PARENTHESIS)

    yield WhileStatement(exp, statement_func(tokens, symbol_table, statement_func), location)


def iteration_statement(tokens, symbol_table, statement_func):
    """
        : 'while' '(' expression ')' statement
        | 'do' statement 'while' '(' expression ')' ';'
        | 'for' '(' expression?; expression?; expression? ')' statement
    """
    return iteration_statement.rules[peek(tokens, default='')](tokens, symbol_table, statement_func)
iteration_statement.rules = defaultdict(lambda: no_rule)
iteration_statement.rules.update({
    TOKENS.WHILE: while_stmnt,
    TOKENS.DO: do_while_stmnt,
    TOKENS.FOR: for_stmnt,
})