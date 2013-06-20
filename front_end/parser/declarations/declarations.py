__author__ = 'samyvilar'

from logging_config import logging
from front_end.loader.locations import loc
from front_end.tokenizer.tokens import TOKENS, IDENTIFIER

from front_end.parser.symbol_table import SymbolTable

from front_end.parser.ast.declarations import EmptyDeclaration, Declaration, Auto, Register, name, FunctionDefinition
from front_end.parser.ast.declarations import TypeDef, Extern, Definition, Declarations
from front_end.parser.ast.declarations import initialization
from front_end.parser.ast.expressions import ConstantExpression, exp, EmptyExpression
from front_end.parser.ast.statements import no_effect, LabelStatement

from front_end.parser.types import CType, FunctionType, StructType, set_core_type, c_type, VoidType

from front_end.parser.declarations.declarators import declarator, storage_class_specifier, type_specifier, type_name

from front_end.parser.expressions.expression import expression

from front_end.errors import error_if_not_type, error_if_not_value


logger = logging.getLogger('parser')


def init_declarator(tokens, symbol_table):  # : declarator ('=' assignment_expression)?
    decl = declarator(tokens, symbol_table)
    if tokens and tokens[0] == TOKENS.EQUAL:
        _ = tokens.pop(0)
        decl.initialization = expression(tokens, symbol_table)
    return decl


def init_declarator_list(tokens, symbol_table):  # init_declarator (',' init_declarator)*
    initialized_declarations = [init_declarator(tokens, symbol_table)]
    while tokens and tokens[0] == TOKENS.COMMA:
        _ = tokens.pop(0)
        initialized_declarations.append(init_declarator(tokens, symbol_table))
    return initialized_declarations


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
    #storage_class_specifier? type_specifier init_declarator_list (';' or compound_statement) # declaration
    if tokens and tokens[0] == TOKENS.TYPEDEF:
        return [type_def(tokens, symbol_table)]

    location = tokens and loc(tokens[0]) or '__EOF__'
    storage_class, base_type = storage_class_specifier(tokens, symbol_table), type_specifier(tokens, symbol_table)

    if tokens and tokens[0] == TOKENS.SEMICOLON:
        declarations, _ = [EmptyDeclaration(location)], tokens.pop(0)
        if not name(base_type):
            logger.warning('{l} Empty declaration'.format(l=loc(base_type)))
        if storage_class:
            logger.warning('{l} Useless storage class {s} for declaration ...'.format(
                l=loc(base_type)), s=storage_class
            )
        return declaration

    declarators = init_declarator_list(tokens, symbol_table)
    for dec in declarators:
        set_core_type(dec, base_type)

    if tokens and tokens[0] in {TOKENS.SEMICOLON, TOKENS.LEFT_BRACE}:
        decls = [
            Definition(name(dec), c_type(dec), initialization(dec), loc(dec), storage_class)
            if initialization(dec) else Declaration(name(dec), c_type(dec), loc(dec), storage_class)
            for dec in (declarators[:-1] if tokens[0] == TOKENS.LEFT_BRACE else declarators)
        ]
        for dec in decls:
            symbol_table[name(dec)] = dec

        if tokens[0] == TOKENS.LEFT_BRACE:  # Function definition.
            decls.append(function_definition(tokens, symbol_table, declarators[-1], storage_class))
        else:
            _ = error_if_not_value(tokens, TOKENS.SEMICOLON)
        return decls

    raise ValueError('{l} Expected "," "=" ";" "{" got {got}'.format(
        l=tokens and loc(tokens[0]) or location, got=tokens and tokens[0])
    )


# specific to compound_statements.
def declaration(tokens, symbol_table):  # storage_class? type_specifier init_declarator_list ';'
    decls = []
    for decl in declarations(tokens, symbol_table):
        if isinstance(decl, FunctionDefinition):
            raise ValueError('{l} Nested function definitions are not allowed.'.format(l=loc(decl)))
        # Non Function declaration without storage class is set to auto
        if type(decl) is Declaration and not decl.storage_class and not isinstance(c_type(decl), FunctionType):
            decl = Definition(name(decl), c_type(decl), EmptyExpression(c_type(decl), loc(decl)), loc(decl), Auto(loc(decl)))
        decls.append(decl)
    return Declarations(decls)


def is_declaration(tokens, symbol_table, rules=set(storage_class_specifier.rules) | set(type_specifier.rules)):
    return tokens and (tokens[0] in rules or isinstance(symbol_table.get(tokens[0]), CType))


# Specific to global scope of file ...
def function_definition(tokens, symbol_table, decl, storage_class):  # : type_specifier declarator compound_statement
    from front_end.parser.statements.compound import statement

    symbol_table.push_frame()
    for arg in c_type(decl):  # add arguments to current scope.
        symbol_table[name(arg)] = arg
    obj = FunctionDefinition(decl, statement(tokens, symbol_table), loc(c_type(decl)), storage_class)
    symbol_table.pop_frame()

    symbol_table[name(decl)] = obj

    for goto_stmnt in symbol_table.goto_stmnts:
        if LabelStatement.get_name(goto_stmnt.label) not in symbol_table.label_stmnts:
            raise ValueError('{l} Could not find label {label} for goto statement {stmnt}'.format(
                l=loc(goto_stmnt), stmnt=goto_stmnt, label=goto_stmnt.label
            ))

    for stmnt in symbol_table.return_stmnts:
        obj.check_return_stmnt(exp(stmnt))
        stmnt.c_type = c_type(exp(stmnt))
    else:
        if not (symbol_table.return_stmnts or isinstance(c_type(c_type(obj)), VoidType)):
            logger.warning('{l} non void function has no return statement.'.format(l=loc(obj)))

    return obj


def type_def(tokens, symbol_table):
    location = loc(tokens.pop(0))
    base_type = type_name(tokens, symbol_table)
    name = error_if_not_type(tokens, IDENTIFIER)
    symbol_table[name] = base_type
    _ = error_if_not_value(tokens, TOKENS.SEMICOLON)
    return TypeDef(name, base_type, location)


def external_declaration(tokens, symbol_table):
    #storage_class_specifier? type_specifier init_declarator_list (';' or compound_statement)
    decls = declarations(tokens, symbol_table)
    for decl in decls:
        if decl and isinstance(decl.storage_class, (Auto, Register)):
            raise ValueError('{l} declarations at file scope may not have {s} storage class'.format(
                l=loc(decl), s=decl.storage_class
            ))
        if initialization(decl) and not isinstance(initialization(decl), ConstantExpression) \
           and not isinstance(decl, FunctionDefinition):
            raise ValueError('{l} definition at file scope may only be initialized with constant expressions'.format(
                l=loc(decl)
            ))
    return decls


def translation_unit(tokens, symbol_table=None):  #: (external_declaration)*
    ext_declarations = []
    symbol_table = symbol_table or SymbolTable()
    while tokens:
        for decl in external_declaration(tokens, symbol_table):
            if not isinstance(decl, EmptyDeclaration):
                ext_declarations.append(decl)
    return ext_declarations