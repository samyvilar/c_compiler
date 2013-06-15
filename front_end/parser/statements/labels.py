__author__ = 'samyvilar'

from collections import defaultdict

from front_end.loader.locations import loc
from front_end.tokenizer.tokens import TOKENS, IDENTIFIER

from front_end.parser.ast.declarations import name
from front_end.parser.ast.statements import LabelStatement, CaseStatement, DefaultStatement
from front_end.parser.types import IntegralType, c_type

from front_end.parser.expressions.expression import constant_expression

from front_end.errors import error_if_not_value, error_if_not_type


def no_rule(tokens, *_):
    raise ValueError('{l} Expected IDENTIFIER:, case, default for got {got}.'.format(l=loc(tokens[0]), got=tokens[0]))


def label(tokens, symbol_table, statement_func, disallowed_statements):
    label_name, _ = tokens.pop(0), error_if_not_value(tokens, TOKENS.COLON)
    stmnt = statement_func(tokens, symbol_table, statement_func, disallowed_statements)
    obj = LabelStatement(label_name, stmnt, loc(label_name))
    symbol_table[name(obj)] = obj
    return obj


def case(tokens, symbol_table, statement_func, disallowed_statements):
    location = loc(loc(tokens.pop(0)))
    if CaseStatement in disallowed_statements:
        raise ValueError('{l} case is not allowed in this context'.format(l=location))
    cons_exp = constant_expression(tokens, symbol_table)
    _, _ = error_if_not_value(tokens, TOKENS.COLON), error_if_not_type(c_type(cons_exp), IntegralType)
    stmnt = statement_func(tokens, symbol_table, statement_func, disallowed_statements)
    return CaseStatement(cons_exp, stmnt, location)


def default(tokens, symbol_table, statement_func, disallowed_statements):
    location, _ = loc(tokens.pop(0)), error_if_not_value(tokens, TOKENS.COLON)
    if DefaultStatement in disallowed_statements:
        raise ValueError('{l} default statement is not allowed in this context'.format(l=location))
    stmnt = statement_func(tokens, symbol_table, statement_func, disallowed_statements)
    return DefaultStatement(stmnt, location)


def labeled_statement(tokens, symbol_table, statement, disallowed_statements):
    """
        : IDENTIFIER ':' statement
        | 'case' constant_expression ':' statement
        | 'default' ':' statement
    """

    if isinstance(tokens[0], IDENTIFIER):
        return label(tokens, symbol_table, statement, disallowed_statements)
    # noinspection PyUnresolvedReferences
    return labeled_statement.rules[tokens[0]](tokens, symbol_table, statement, disallowed_statements)
labeled_statement.rules = defaultdict(lambda: no_rule)
labeled_statement.rules.update({
    TOKENS.CASE: case,
    TOKENS.DEFAULT: default
})