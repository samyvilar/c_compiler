__author__ = 'samyvilar'

from collections import defaultdict

from sequences import peek, consume

from front_end.loader.locations import loc, EOFLocation
from front_end.tokenizer.tokens import TOKENS, IDENTIFIER

from front_end.parser.ast.expressions import exp
from front_end.parser.ast.statements import LabelStatement, CaseStatement, DefaultStatement
from front_end.parser.types import IntegralType, c_type

from front_end.parser.expressions.expression import constant_expression

from front_end.errors import error_if_not_value, error_if_not_type


def no_rule(tokens, *_):
    raise ValueError('{l} Expected IDENTIFIER:, case, default got {got}.'.format(
        l=loc(peek(tokens, EOFLocation)), got=peek(tokens, '')
    ))


def label(tokens, symbol_table, statement_func):
    label_name, _ = consume(tokens), error_if_not_value(tokens, TOKENS.COLON)
    yield LabelStatement(
        label_name, statement_func(tokens, symbol_table, statement_func), loc(label_name)
    )


def case(tokens, symbol_table, statement_func):
    location = loc(loc(consume(tokens)))
    expr = constant_expression(tokens, symbol_table)
    _, _ = error_if_not_value(tokens, TOKENS.COLON), error_if_not_type(c_type(expr), IntegralType)
    switch = symbol_table['__ SWITCH STATEMENT __']
    if exp(expr) in switch:
        raise ValueError('{l} duplicate case statement previous at {p}'.format(l=location, p=loc(switch[exp(expr)])))
    switch[exp(expr)] = CaseStatement(expr, statement_func(tokens, symbol_table, statement_func), location)
    yield switch[exp(expr)]


def default(tokens, symbol_table, statement_func):
    location, _ = loc(consume(tokens)), error_if_not_value(tokens, TOKENS.COLON)
    switch = symbol_table['__ SWITCH STATEMENT __']
    if 'default' in switch:
        raise ValueError('{l} duplicate default statement previous at {p}'.format(l=location, p=loc(switch['default'])))
    switch['default'] = DefaultStatement(statement_func(tokens, symbol_table, statement_func), location)
    yield switch['default']


def labeled_statement(tokens, symbol_table, statement):
    """
        : IDENTIFIER ':' statement
        | 'case' constant_expression ':' statement
        | 'default' ':' statement
    """

    if isinstance(peek(tokens), IDENTIFIER):
        return label(tokens, symbol_table, statement)
    # noinspection PyUnresolvedReferences

    try:
        _ = symbol_table['__ SWITCH STATEMENT __']
    except KeyError as _:
        raise ValueError('{l} {g} statement outside of switch'.format(l=loc(peek(tokens)), g=peek(tokens)))

    return labeled_statement.rules[peek(tokens)](tokens, symbol_table, statement)
labeled_statement.rules = defaultdict(lambda: no_rule)
labeled_statement.rules.update({
    TOKENS.CASE: case,
    TOKENS.DEFAULT: default
})