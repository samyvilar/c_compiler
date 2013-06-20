__author__ = 'samyvilar'

from collections import defaultdict

from front_end.loader.locations import loc, LocationNotSet
from front_end.tokenizer.tokens import TOKENS

from front_end.parser.ast.statements import IfStatement, ElseStatement, SwitchStatement, EmptyStatement
from front_end.parser.ast.statements import CaseStatement, DefaultStatement, BreakStatement
from front_end.parser.expressions.expression import expression

from front_end.errors import error_if_not_value


def no_rule(tokens, *args):
    raise ValueError('{l} selection_statement expected either "if" or "switch: got {got}'.format(
        got=tokens[0], l=loc(tokens[0])
    ))


def _if(tokens, symbol_table, statement, disallowed_statements):
    location = loc(tokens.pop(0))
    _ = error_if_not_value(tokens, TOKENS.LEFT_PARENTHESIS)
    exp = expression(tokens, symbol_table)
    _ = error_if_not_value(tokens, TOKENS.RIGHT_PARENTHESIS)

    stmnt = statement(tokens, symbol_table, disallowed_statements=disallowed_statements)

    else_stmnt = EmptyStatement(LocationNotSet)
    if tokens and tokens[0] == TOKENS.ELSE:
        else_location = loc(tokens.pop(0))
        else_stmnt = ElseStatement(
            statement(tokens, symbol_table, disallowed_statements=disallowed_statements),
            else_location
        )
    return IfStatement(exp, stmnt, else_stmnt, location)


def switch(tokens, symbol_table, statement, disallowed_statements):
    location = loc(tokens.pop(0))
    _ = error_if_not_value(tokens, TOKENS.LEFT_PARENTHESIS)
    exp = expression(tokens, symbol_table)
    _ = error_if_not_value(tokens, TOKENS.RIGHT_PARENTHESIS)
    return SwitchStatement(
        exp,
        statement(
            tokens,
            symbol_table,
            disallowed_statements=set(disallowed_statements) - {CaseStatement, DefaultStatement, BreakStatement},
        ),
        location
    )


def selection_statement(tokens, symbol_table, statement, disallowed_statements):
    """
        : 'if' '(' expression ')' statement ('else' statement)?
        | 'switch' '(' expression ')' statement
    """
    return selection_statement.rules[tokens[0]](tokens, symbol_table, statement, disallowed_statements)
selection_statement.rules = defaultdict(lambda: no_rule)
selection_statement.rules.update({
    TOKENS.IF:_if,
    TOKENS.SWITCH:switch,
})