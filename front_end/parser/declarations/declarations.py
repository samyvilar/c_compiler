__author__ = 'samyvilar'

from types import NoneType
from itertools import starmap, product, chain, repeat

from utils.sequences import peek, consume, flatten, takewhile
from logging_config import logging
from front_end.loader.locations import loc, EOFLocation
from front_end.tokenizer.tokens import TOKENS

from front_end.parser.symbol_table import SymbolTable, push, pop

from front_end.parser.ast.statements import CompoundStatement, FunctionDefinition
from front_end.parser.ast.declarations import EmptyDeclaration, Declaration, Auto, Register, name
from front_end.parser.ast.declarations import Extern, Definition, TypeDef
from front_end.parser.ast.declarations import initialization
from front_end.parser.ast.expressions import ConstantExpression, EmptyExpression, exp

from front_end.parser.types import CType, StructType, set_core_type, c_type, FunctionType, VAListType, StringType
from front_end.parser.types import ArrayType, CharType

from front_end.parser.declarations.declarators import declarator, storage_class_specifier
from front_end.parser.declarations.declarators import type_specifier, specifier_qualifier_list

from front_end.parser.expressions.expression import assignment_expression, cast_expression, initializer

from front_end.errors import error_if_not_value

logger = logging.getLogger('parser')


def init_declarator(tokens, symbol_table, base_type=CType('')):
    # : declarator ('=' assignment_expression or initializer)?
    decl = declarator(tokens, symbol_table)
    set_core_type(decl, base_type)
    if peek(tokens, '') == TOKENS.EQUAL:
        _ = consume(tokens)
        decl = Definition(name(decl), c_type(decl), None, loc(decl), None)
        symbol_table[name(decl)] = decl  # we have to add it to the symbol table for things like `int a = a;`
        assert not isinstance(c_type(decl), FunctionType)

        if peek(tokens, '') == TOKENS.LEFT_BRACE:
            expr = initializer(tokens, symbol_table, c_type(decl))
            decl.initialization = (
                all(starmap(isinstance, product(flatten(exp(expr)), (ConstantExpression,)))) and
                ConstantExpression(exp(expr), c_type(expr), loc(expr))
            ) or expr
        else:
            decl.initialization = assignment_expression(tokens, symbol_table, cast_expression)

        ctype = c_type(decl.initialization)
        if isinstance(c_type(decl), ArrayType) and isinstance(c_type(c_type(decl)), CharType) and \
                isinstance(ctype, StringType):
            decl.initialization = ConstantExpression(
                [next(
                    exp(decl.initialization),
                    ConstantExpression(ord('\0'), CharType(loc(ctype)), loc(ctype)))
                 for _ in xrange(len(c_type(decl)))],
                ArrayType(CharType(loc(ctype)), len(c_type(decl)), loc(ctype)),
                loc(decl.initialization)
            )
    else:
        decl = Declaration(name(decl), c_type(decl), loc(decl))
        symbol_table[name(decl)] = decl
    return decl


def init_declarator_list(tokens, symbol_table, base_type=CType('')):  # init_declarator (',' init_declarator)*
    yield init_declarator(tokens, symbol_table, base_type=base_type)
    while peek(tokens) == TOKENS.COMMA:
        _ = consume(tokens)
        yield init_declarator(tokens, symbol_table, base_type=base_type)


def get_declaration_or_definition(decl, storage_class):
    if initialization(decl) and isinstance(storage_class, Extern):
        raise ValueError('{l} {ident} has both initialization expr and extern storage class'.format(
            l=loc(decl), ident=name(decl),
        ))

    if isinstance(c_type(decl), (FunctionType, StructType)) and not name(decl) or isinstance(storage_class, Extern):
        return Declaration(name(decl), c_type(decl), loc(decl), storage_class)

    return Definition(name(decl), c_type(decl), initialization(decl), loc(decl), storage_class or Auto(loc(decl)))


def declarations(tokens, symbol_table):
    # storage_class_specifier? type_name? init_declarator_list (';' or compound_statement) # declaration
    storage_class = storage_class_specifier(tokens, symbol_table)
    base_type = specifier_qualifier_list(tokens, symbol_table)

    from front_end.parser.statements.compound import statement

    if peek(tokens, '') == TOKENS.SEMICOLON:
        yield EmptyDeclaration(loc(consume(tokens)), storage_class)
    elif peek(tokens, ''):
        obj = None
        for dec in init_declarator_list(tokens, symbol_table, base_type=base_type):
            dec.storage_class = storage_class
            if isinstance(storage_class, TypeDef):  # init_declarator_list adds the symbol as a decl to symbol_table
                _ = symbol_table.pop(name(dec))
                symbol_table[name(dec)] = c_type(dec)  # add the new symbol as a CType...
                obj = TypeDef(name(dec), c_type(dec), loc(dec))
            elif peek(tokens, '') == TOKENS.LEFT_BRACE:
                push(symbol_table)
                for arg in c_type(dec):  # add parameters to scope.
                    if not isinstance(c_type(arg), VAListType):
                        symbol_table[name(arg)] = arg
                symbol_table['__ RETURN_TYPE __'] = c_type(c_type(dec))
                obj = FunctionDefinition(dec, next(statement(tokens, symbol_table)))
            else:
                obj = dec
            yield obj
            if isinstance(obj, FunctionDefinition):
                _ = pop(symbol_table)
                break
        _ = obj and not isinstance(obj, FunctionDefinition) and error_if_not_value(tokens, TOKENS.SEMICOLON)
    else:
        raise ValueError('{l} Expected `,` `=` `;` `{{` got {got}'.format(
            l=loc(peek(tokens, EOFLocation)), got=peek(tokens, '')
        ))


# specific to compound_statements.
def declaration(tokens, symbol_table):  # storage_class? type_specifier init_declarator_list ';'
    for decl in declarations(tokens, symbol_table):
        if isinstance(decl, FunctionDefinition):
            raise ValueError('{l} Nested function definitions are not allowed.'.format(l=loc(decl)))
        # Non Function declaration without storage class is set to auto
        if type(decl) is Declaration and not isinstance(c_type(decl), FunctionType):
            decl = Definition(
                name(decl),
                c_type(decl),
                EmptyExpression(c_type(decl), loc(decl)),
                loc(decl),
                decl.storage_class or Auto(loc(decl))
            )
        yield decl


def is_declaration(
        tokens,
        symbol_table,
        rules=set(storage_class_specifier.rules) | set(type_specifier.rules) | {TOKENS.CONST, TOKENS.VOLATILE}
):
    return peek(tokens, '') in rules or isinstance(symbol_table.get(peek(tokens, ''), ''), CType)


def external_declaration(tokens, symbol_table):
    #storage_class_specifier? type_specifier init_declarator_list (';' or compound_statement)
    for decl in declarations(tokens, symbol_table):
        if decl and isinstance(decl.storage_class, (Auto, Register)):
            raise ValueError('{l} declarations at file scope may not have {s} storage class'.format(
                l=loc(decl), s=decl.storage_class
            ))

        if not isinstance(
                initialization(decl, ConstantExpression(0, None)),
                (NoneType, ConstantExpression, CompoundStatement)
        ):
            raise ValueError(
                '{l} definition at file scope may only be initialized with constant expressions, got {g}'.format(
                    l=loc(decl), g=initialization(decl)
                )
            )
        yield decl


def translation_unit(tokens, symbol_table=None):  #: (external_declaration)*
    symbol_table = symbol_table or SymbolTable()
    return chain.from_iterable(
        starmap(external_declaration, takewhile(lambda args: peek(args[0]), repeat((tokens, symbol_table))))
    )