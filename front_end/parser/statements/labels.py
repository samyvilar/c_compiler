__author__ = 'samyvilar'

from itertools import imap

from utils.sequences import peek, consume
from utils.rules import rules, set_rules

from front_end.loader.locations import loc
from front_end.tokenizer.tokens import TOKENS, IDENTIFIER

from front_end.parser.ast.expressions import exp
from front_end.parser.ast.statements import LabelStatement, CaseStatement, DefaultStatement
from front_end.parser.types import IntegralType, c_type


from utils.errors import error_if_not_value, error_if_not_type


def label(tokens, symbol_table):
    label_name, _ = consume(tokens), error_if_not_value(tokens, TOKENS.COLON)
    symbol_table['__ LABELS __'][label_name] = label = LabelStatement(
        label_name, symbol_table['__ statement __'](tokens, symbol_table), loc(label_name)
    )
    yield label


def case(tokens, symbol_table):
    location = loc(loc(consume(tokens)))
    constant_expression, statement = imap(symbol_table.__getitem__, ('__ constant_expression __', '__ statement __'))
    expr = constant_expression(tokens, symbol_table)
    _, _ = error_if_not_value(tokens, TOKENS.COLON), error_if_not_type(c_type(expr), IntegralType)
    switch_cases = symbol_table['__ SWITCH STATEMENT __']
    switch_exp = symbol_table['__ SWITCH EXPRESSION __']
    if c_type(expr) != c_type(switch_exp):
        raise ValueError('{l} case exp type {g} differs from switch exp type {e}'.format(
            l=location, g=c_type(expr), e=c_type(switch_exp)
        ))
    switch_cases[exp(expr)] = CaseStatement(expr, statement(tokens, symbol_table), location)
    yield switch_cases[exp(expr)]


def default(tokens, symbol_table):
    location, _ = loc(consume(tokens)), error_if_not_value(tokens, TOKENS.COLON)
    switch = symbol_table['__ SWITCH STATEMENT __']
    switch['default'] = DefaultStatement(symbol_table['__ statement __'](tokens, symbol_table), location)
    yield switch['default']


def labeled_statement(tokens, symbol_table):
    """
        : IDENTIFIER ':' statement
        | 'case' constant_expression ':' statement
        | 'default' ':' statement
    """

    if isinstance(peek(tokens), IDENTIFIER):
        return label(tokens, symbol_table)

    try:
        _ = symbol_table['__ SWITCH STATEMENT __']
    except KeyError as _:
        raise ValueError('{l} {g} statement outside of switch'.format(l=loc(peek(tokens)), g=peek(tokens)))

    return rules(labeled_statement)[peek(tokens)](tokens, symbol_table)
set_rules(labeled_statement, ((TOKENS.CASE, case), (TOKENS.DEFAULT, default)))