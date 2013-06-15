__author__ = 'samyvilar'

from collections import defaultdict

from front_end.loader.locations import loc
from front_end.tokenizer.tokens import TOKENS

from front_end.parser.ast.statements import ForStatement, WhileStatement, DoWhileStatement
from front_end.parser.ast.statements import ContinueStatement, BreakStatement
from front_end.parser.ast.expressions import EmptyExpression, TrueExpression
from front_end.parser.expressions.expression import expression
from front_end.errors import error_if_not_value


def no_rule(tokens, *_):
    raise ValueError('{l} expected either "for", "while", or "do" got {got}'.format(
        l=loc(tokens[0]), got=tokens[0]
    ))


def for_stmnt(tokens, symbol_table, statement_func, disallowed_statements):
    location, _ = loc(tokens.pop(0)), error_if_not_value(tokens, TOKENS.LEFT_PARENTHESIS)

    init_exp = EmptyExpression(location=location)
    if tokens and tokens[0] != TOKENS.SEMICOLON:
        init_exp = expression(tokens, symbol_table)
    _ = error_if_not_value(tokens, TOKENS.SEMICOLON)

    conditional_exp = TrueExpression(location=location)
    if tokens and tokens[0] != TOKENS.SEMICOLON:
        conditional_exp = expression(tokens, symbol_table)
    _ = error_if_not_value(tokens, TOKENS.SEMICOLON)

    update_exp = EmptyExpression(location=location)
    if tokens and tokens[0] != TOKENS.SEMICOLON:
        update_exp = expression(tokens, symbol_table)

    _ = error_if_not_value(tokens, TOKENS.RIGHT_PARENTHESIS)
    return ForStatement(
        init_exp,
        conditional_exp,
        update_exp,
        statement_func(tokens, symbol_table, statement_func, disallowed_statements),
        location
    )


def do_while_stmnt(tokens, symbol_table, statement_func, disallowed_statements):
    location = loc(tokens.pop(0))
    stmnt = statement_func(tokens, symbol_table, statement_func, disallowed_statements)

    _, _ = error_if_not_value(tokens, TOKENS.WHILE), error_if_not_value(tokens, TOKENS.LEFT_PARENTHESIS)
    exp = expression(tokens, symbol_table)
    _, _ = error_if_not_value(tokens, TOKENS.RIGHT_PARENTHESIS), error_if_not_value(tokens, TOKENS.SEMICOLON)

    return DoWhileStatement(exp, stmnt, location)


def while_stmnt(tokens, symbol_table, statement_func, disallowed_statements):
    location = loc(tokens.pop(0))
    _ = error_if_not_value(tokens, TOKENS.LEFT_PARENTHESIS)
    exp = expression(tokens, symbol_table)
    _ = error_if_not_value(tokens, TOKENS.RIGHT_PARENTHESIS)

    return WhileStatement(exp, statement_func(tokens, symbol_table, disallowed_statements=disallowed_statements), location)


def iteration_statement(tokens, symbol_table, statement_func, disallowed_statements):
    """
        : 'while' '(' expression ')' statement
        | 'do' statement 'while' '(' expression ')' ';'
        | 'for' '(' expression?; expression?; expression?; ')' statement
    """
    return iteration_statement.rules[tokens[0]](
        tokens,
        symbol_table,
        statement_func,
        set(disallowed_statements) - {BreakStatement, ContinueStatement}
    )
iteration_statement.rules = defaultdict(lambda: no_rule)
iteration_statement.rules.update({
    TOKENS.WHILE: while_stmnt,
    TOKENS.DO: do_while_stmnt,
    TOKENS.FOR: for_stmnt,
})