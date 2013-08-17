__author__ = 'samyvilar'

from types import NoneType
from sequences import peek, consume
from logging_config import logging
from front_end.loader.locations import loc, EOFLocation
from front_end.tokenizer.tokens import TOKENS

from front_end.parser.symbol_table import SymbolTable, push, pop

from front_end.parser.ast.statements import CompoundStatement, FunctionDefinition
from front_end.parser.ast.declarations import EmptyDeclaration, Declaration, Auto, Register, name, Static
from front_end.parser.ast.declarations import Extern, Definition, TypeDef
from front_end.parser.ast.declarations import initialization
from front_end.parser.ast.expressions import ConstantExpression, EmptyExpression

from front_end.parser.types import CType, StructType, set_core_type, c_type, FunctionType, VAListType

from front_end.parser.declarations.declarators import declarator, storage_class_specifier
from front_end.parser.declarations.declarators import type_specifier, specifier_qualifier_list

from front_end.parser.expressions.expression import expression

from front_end.errors import error_if_not_value

logger = logging.getLogger('parser')


def init_declarator(tokens, symbol_table, base_type=CType('')):  # : declarator ('=' assignment_expression)?
    decl = declarator(tokens, symbol_table)
    set_core_type(decl, base_type)
    if peek(tokens, default='') == TOKENS.EQUAL:
        _ = consume(tokens)
        decl = Definition(name(decl), c_type(decl), None, loc(decl), None)
        symbol_table[name(decl)] = decl
        assert not isinstance(c_type(decl), FunctionType)
        decl.initialization = expression(tokens, symbol_table)
    else:
        decl = Declaration(name(decl), c_type(decl), loc(decl))
        symbol_table[name(decl)] = decl
    return decl


def init_declarator_list(tokens, symbol_table, base_type=CType('')):  # init_declarator (',' init_declarator)*
    yield init_declarator(tokens, symbol_table, base_type=base_type)
    while peek(tokens, default='') == TOKENS.COMMA:
        _ = consume(tokens)
        yield init_declarator(tokens, symbol_table, base_type=base_type)


def get_declaration_or_definition(decl, storage_class):
    if initialization(decl) and isinstance(storage_class, Extern):
        raise ValueError('{l} {ident} has both initialization expr and extern storage class'.format(
            l=loc(decl), ident=name(decl),
        ))

    if isinstance(c_type(decl), (FunctionType, StructType)) and not name(decl) or isinstance(storage_class, Extern):
        return Declaration(name(decl), c_type(decl), loc(decl), storage_class)

    return Definition(
        name(decl), c_type(decl), initialization(decl), loc(decl), storage_class or Auto(loc(decl))
    )


def declarations(tokens, symbol_table):
    # storage_class_specifier? type_name? init_declarator_list (';' or compound_statement) # declaration
    storage_class = storage_class_specifier(tokens, symbol_table)
    base_type = specifier_qualifier_list(tokens, symbol_table)

    from front_end.parser.statements.compound import statement

    if peek(tokens, default='') == TOKENS.SEMICOLON:
        yield EmptyDeclaration(loc(consume(tokens)), storage_class)
    elif peek(tokens, default=''):
        obj = None
        for dec in init_declarator_list(tokens, symbol_table, base_type=base_type):
            dec.storage_class = storage_class
            if isinstance(storage_class, TypeDef):
                _ = symbol_table.pop(name(dec))
                symbol_table[name(dec)] = c_type(dec)
                obj = TypeDef(name(dec), c_type(dec), loc(dec))
            elif peek(tokens, default='') == TOKENS.LEFT_BRACE:
                push(symbol_table)
                for arg in c_type(dec):  # add parameters to scope.
                    if not isinstance(c_type(arg), VAListType):
                        symbol_table[name(arg)] = arg
                obj = FunctionDefinition(dec, next(statement(tokens, symbol_table)))
            else:
                obj = dec
            yield obj
            if isinstance(obj, FunctionDefinition):
                _ = pop(symbol_table)
                break
        if obj and not isinstance(obj, FunctionDefinition):
            _ = error_if_not_value(tokens, TOKENS.SEMICOLON)
    else:
        raise ValueError('{l} Expected "," "=" ";" LEFT_BRACE got {got}'.format(
            l=loc(peek(tokens, default='')) or '__EOF__', got=peek(tokens, default='')
        ))


# specific to compound_statements.
def declaration(tokens, symbol_table):  # storage_class? type_specifier init_declarator_list ';'
    for decl in declarations(tokens, symbol_table):
        if isinstance(decl, FunctionDefinition):
            raise ValueError('{l} Nested function definitions are not allowed.'.format(l=loc(decl)))
        # Non Function declaration without storage class is set to auto
        if type(decl) is Declaration and not decl.storage_class and not isinstance(c_type(decl), FunctionType) or \
           isinstance(decl.storage_class, Static):
            decl = Definition(
                name(decl),
                c_type(decl),
                EmptyExpression(c_type(decl), loc(decl)),
                loc(decl),
                Auto(loc(decl))
            )
        yield decl


def is_declaration(
        tokens,
        symbol_table,
        rules=set(storage_class_specifier.rules) | set(type_specifier.rules) | {TOKENS.CONST, TOKENS.VOLATILE}
):
    return peek(tokens, default='') in rules or isinstance(symbol_table.get(peek(tokens, default=''), ''), CType)


def external_declaration(tokens, symbol_table):
    #storage_class_specifier? type_specifier init_declarator_list (';' or compound_statement)
    for decl in declarations(tokens, symbol_table):
        if decl and isinstance(decl.storage_class, (Auto, Register)):
            raise ValueError('{l} declarations at file scope may not have {s} storage class'.format(
                l=loc(decl), s=decl.storage_class
            ))
        if not isinstance(initialization(decl, ConstantExpression(0, '', '')),
                          (NoneType, ConstantExpression, CompoundStatement)):
            raise ValueError(
                '{l} definition at file scope may only be initialized with constant expressions, got {g}'.format(
                    l=loc(decl), g=initialization(decl, ConstantExpression(0, '', ''))
                )
            )
        yield decl


def translation_unit(tokens, symbol_table=None):  #: (external_declaration)*
    symbol_table = symbol_table or SymbolTable()
    while peek(tokens, default=''):
        for decl in external_declaration(tokens, symbol_table):
            yield decl