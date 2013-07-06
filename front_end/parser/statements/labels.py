__author__ = 'samyvilar'

from collections import defaultdict

from sequences import peek, consume

from front_end.loader.locations import loc
from front_end.tokenizer.tokens import TOKENS, IDENTIFIER

from front_end.parser.ast.statements import LabelStatement, CaseStatement, DefaultStatement
from front_end.parser.types import IntegralType, c_type

from front_end.parser.expressions.expression import constant_expression

from front_end.errors import error_if_not_value, error_if_not_type


def no_rule(tokens, *_):
    raise ValueError('{l} Expected IDENTIFIER:, case, default got {got}.'.format(
        l=loc(peek(tokens, default='')) or '__EOF__', got=peek(tokens, default='')
    ))


def label(tokens, symbol_table, statement_func):
    label_name, _ = consume(tokens), error_if_not_value(tokens, TOKENS.COLON)
    yield LabelStatement(
        label_name, statement_func(tokens, symbol_table, statement_func), loc(label_name)
    )


def case(tokens, symbol_table, statement_func):
    location = loc(loc(consume(tokens)))
    exp = constant_expression(tokens, symbol_table)
    _, _ = error_if_not_value(tokens, TOKENS.COLON), error_if_not_type([c_type(exp)], IntegralType)
    yield CaseStatement(exp, statement_func(tokens, symbol_table, statement_func), location)


def default(tokens, symbol_table, statement_func):
    location, _ = loc(consume(tokens)), error_if_not_value(tokens, TOKENS.COLON)
    yield DefaultStatement(statement_func(tokens, symbol_table, statement_func), location)


def labeled_statement(tokens, symbol_table, statement):
    """
        : IDENTIFIER ':' statement
        | 'case' constant_expression ':' statement
        | 'default' ':' statement
    """

    if isinstance(peek(tokens), IDENTIFIER):
        return label(tokens, symbol_table, statement)
    # noinspection PyUnresolvedReferences
    return labeled_statement.rules[peek(tokens)](tokens, symbol_table, statement)
labeled_statement.rules = defaultdict(lambda: no_rule)
labeled_statement.rules.update({
    TOKENS.CASE: case,
    TOKENS.DEFAULT: default
})