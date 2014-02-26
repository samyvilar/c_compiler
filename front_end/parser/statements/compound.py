__author__ = 'samyvilar'

from itertools import chain, izip, repeat, imap

from utils.sequences import peek, consume, terminal, peek_or_terminal, consume_all
from utils.rules import rules, set_rules
from utils.symbol_table import get_symbols

from front_end.loader.locations import loc, EOFLocation
from front_end.tokenizer.tokens import TOKENS, IDENTIFIER
from front_end.parser.types import CType, c_type, FunctionType
from utils.symbol_table import push, pop

from front_end.parser.ast.declarations import Definition, Declaration, name, Auto, Extern
from front_end.parser.ast.expressions import EmptyExpression
from front_end.parser.ast.statements import EmptyStatement, CompoundStatement, FunctionDefinition

from front_end.parser.statements.labels import labeled_statement
from front_end.parser.statements.selections import selection_statement
from front_end.parser.statements.iterations import iteration_statement
from front_end.parser.statements.jumps import jump_statement

from utils.errors import error_if_not_value, raise_error


def _empty_statement(tokens, *_):
    yield EmptyStatement(loc(error_if_not_value(tokens, TOKENS.SEMICOLON)))


def compound_statement(tokens, symbol_table):  #: '{' statement*  '}'
    _, symbol_table = error_if_not_value(tokens, TOKENS.LEFT_BRACE), push(symbol_table)
    statement = symbol_table['__ statement __']
    while peek(tokens, TOKENS.RIGHT_BRACE) != TOKENS.RIGHT_BRACE:
        yield statement(tokens, symbol_table)
    _ = error_if_not_value(tokens, TOKENS.RIGHT_BRACE) and pop(symbol_table)


def _comp_stmnt(tokens, symbol_table):
    yield CompoundStatement(compound_statement(tokens, symbol_table), loc(peek(tokens)))


def convert_declaration_to_definition(decl):
    _ = isinstance(decl, FunctionDefinition) and raise_error(
        '{l} Nested function definitions are not allowed.'.format(l=loc(decl)))
    # Non Function declaration without storage class is set to auto
    if type(decl) is Declaration and not isinstance(c_type(decl), FunctionType) and decl.storage_class is not Extern:
        decl = Definition(  # all non-function-declarations within compound statements are definitions ...
            name(decl),
            c_type(decl),
            EmptyExpression(c_type(decl), loc(decl)),
            loc(decl),
            decl.storage_class or Auto(loc(decl))
        )
    return decl


# specific to compound_statements.
def declaration(tokens, symbol_table):  # storage_class? type_specifier init_declarator_list ';'
    return imap(convert_declaration_to_definition, symbol_table['__ declarations __'](tokens, symbol_table))


def is_declaration(tokens, symbol_table):
    funcs = '__ storage_class_specifier __', '__ type_specifier __', '__ type_qualifiers __'
    val = peek_or_terminal(tokens)
    return any(chain(
        imap(
            apply, imap(getattr, imap(rules, get_symbols(symbol_table, *funcs)), repeat('__contains__')), repeat((val,))
        ),
        (isinstance(symbol_table.get(val, val), CType),)
    ))


def statement(tokens, symbol_table):
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
    if peek_or_terminal(tokens) in rules(statement):  # if current token has a rule use that one first
        return rules(statement)[peek(tokens)](tokens, symbol_table)

    if is_declaration(tokens, symbol_table):  # checking for type_name is a bit expensive ...
        return declaration(tokens, symbol_table)

    # both expressions and labels may start with an identifier
    if isinstance(peek_or_terminal(tokens), IDENTIFIER):
        label_name = consume(tokens)
        if peek_or_terminal(tokens) == TOKENS.COLON:
            return symbol_table['__ labeled_statement __'](chain((label_name,), consume_all(tokens)), symbol_table)
            # return label_stmnt(label_name, statement(tokens, symbol_table))
        # it must be an expression, TODO: figure out a way without using dangerous chain!
        # tokens = chain((label_name, consume(tokens)), tokens)
        tokens = chain((label_name,),  consume_all(tokens))
        expr, _ = symbol_table['__ expression __'](tokens, symbol_table), error_if_not_value(tokens, TOKENS.SEMICOLON)
        return repeat(expr, 1)

    if peek_or_terminal(tokens) is not terminal:
        expr, _ = symbol_table['__ expression __'](tokens, symbol_table), error_if_not_value(tokens, TOKENS.SEMICOLON)
        return repeat(expr, 1)

    raise ValueError('{l} No rule could be found to create statement, got {got}'.format(
        l=loc(peek(tokens, EOFLocation)), got=peek(tokens, '')
    ))
statement_funcs = labeled_statement, selection_statement, iteration_statement, jump_statement
set_rules(
    statement,
    chain(
        chain.from_iterable(imap(izip, imap(rules, statement_funcs), imap(repeat, statement_funcs))),
        ((TOKENS.LEFT_BRACE, _comp_stmnt), (TOKENS.SEMICOLON, _empty_statement))
    )
)