__author__ = 'samyvilar'

from itertools import ifilterfalse, imap, chain, repeat, takewhile, starmap

from utils.sequences import peek, peek_or_terminal, consume, terminal
from utils.rules import set_rules, rules
from front_end.loader.locations import loc, EOFLocation
from front_end.tokenizer.tokens import TOKENS

from utils.symbol_table import push, pop, SymbolTable

from front_end.parser.ast.declarations import EmptyDeclaration, Declaration, Auto, Register, name
from front_end.parser.ast.declarations import Extern, Definition, TypeDef
from front_end.parser.ast.declarations import initialization
from front_end.parser.ast.statements import FunctionDefinition
from front_end.parser.ast.expressions import Initializer, EmptyExpression, ConstantExpression, exp

from front_end.parser.types import CType, StructType, set_core_type, c_type, FunctionType, VAListType, StringType
from front_end.parser.types import ArrayType

from front_end.parser.expressions.initializer import parse_initializer, initializer_defaults


from utils.errors import error_if_not_value, error_if_not_type, raise_error


def _assignment_expression(tokens, symbol_table):
    return symbol_table['__ assignment_expression __'](tokens, symbol_table)


def _initializer_expression(tokens, symbol_table):
    return symbol_table['__ initializer __'](tokens, symbol_table)


def initializer_or_assignment_expression(tokens, symbol_table):
    return rules(initializer_or_assignment_expression)[peek(tokens)](tokens, symbol_table)
set_rules(initializer_or_assignment_expression, ((TOKENS.LEFT_BRACE, _initializer_expression),), _assignment_expression)


def init_declarator(tokens, symbol_table, base_type=CType(''), storage_class=None):
    # : declarator ('=' assignment_expression or initializer)?
    decl = set_core_type(symbol_table['__ declarator __'](tokens, symbol_table), base_type)
    if peek_or_terminal(tokens) == TOKENS.EQUAL and consume(tokens):
        decl = Definition(name(decl), c_type(decl), EmptyExpression(c_type(decl)), loc(decl), storage_class)
        symbol_table[name(decl)] = decl  # we have to add it to the symbol table for things like `int a = a;`
        expr = initializer_or_assignment_expression(tokens, symbol_table)
        # if declaration is an array type and the expression is of string_type then convert to initializer for parsing
        if isinstance(c_type(decl), ArrayType) and isinstance(c_type(expr), StringType):
            expr = Initializer(
                enumerate(exp(expr)), ArrayType(c_type(c_type(expr)), len(c_type(expr)), loc(expr)), loc(expr)
            )
        decl.initialization = parse_initializer(expr, decl) if isinstance(expr, Initializer) else expr
    else:
        symbol_table[name(decl)] = decl = Declaration(name(decl), c_type(decl), loc(decl))
    return decl


def init_declarator_list(tokens, symbol_table, base_type=CType(''), storage_class=None):
    return chain(   # init_declarator (',' init_declarator)*
        (init_declarator(tokens, symbol_table, base_type=base_type, storage_class=storage_class),),
        starmap(
            init_declarator,
            takewhile(
                lambda i: peek(i[0]) == TOKENS.COMMA and consume(i[0]),
                repeat((tokens, symbol_table, base_type, storage_class))
            )
        )
    )


def get_declaration_or_definition(decl, storage_class):
    _ = initialization(decl) and isinstance(storage_class, Extern) and raise_error(
        '{l} {ident} has both initialization expr and extern storage class'.format(l=loc(decl), ident=name(decl)))

    if isinstance(c_type(decl), (FunctionType, StructType)) and not name(decl) or isinstance(storage_class, Extern):
        return Declaration(name(decl), c_type(decl), loc(decl), storage_class)

    return Definition(name(decl), c_type(decl), initialization(decl), loc(decl), storage_class or Auto(loc(decl)))


def declarations(tokens, symbol_table):
    # storage_class_specifier? type_name? init_declarator_list (';' or compound_statement) # declaration
    storage_class_specifier, specifier_qualifier_list, statement = imap(
        symbol_table.__getitem__,
        ('__ storage_class_specifier __', '__ specifier_qualifier_list __', '__ statement __')
    )
    storage_class = storage_class_specifier(tokens, symbol_table)
    base_type = specifier_qualifier_list(tokens, symbol_table)

    expecting_token = TOKENS.SEMICOLON
    if peek_or_terminal(tokens) == TOKENS.SEMICOLON:
        yield EmptyDeclaration(loc(consume(tokens)), storage_class)
    elif peek_or_terminal(tokens) is terminal:
        raise_error('{l} Expected TOKENS.COMMA TOKENS.EQUAL TOKENS.SEMICOLON TOKENS.LEFT_BRACE got `{got}`'.format(
            l=loc(peek(tokens, EOFLocation)), got=peek(tokens, '')
        ))
    else:
        for dec in init_declarator_list(tokens, symbol_table, base_type=base_type, storage_class=storage_class):
            dec.storage_class = storage_class
            if isinstance(storage_class, TypeDef):  # init_declarator_list adds the symbol as a decl to symbol_table
                symbol_table[name(dec)] = (symbol_table.pop(name(dec)) or 1) and c_type(dec)  # replace dec by ctype
            elif peek_or_terminal(tokens) == TOKENS.LEFT_BRACE and not error_if_not_type(c_type(dec), FunctionType):
                symbol_table = push(symbol_table)
                symbol_table.update(chain(
                    imap(
                        lambda a: (name(a), a),  # add non variable list parameters to the symbol table ...
                        ifilterfalse(lambda c: isinstance(c_type(c), VAListType), c_type(dec))
                    ),
                    (('__ RETURN_TYPE __', c_type(c_type(dec))), ('__ LABELS __', SymbolTable()))
                ))
                yield FunctionDefinition(dec, next(statement(tokens, symbol_table)))
                expecting_token = (pop(symbol_table) or 1) and ''
            else:
                yield dec
                expecting_token = TOKENS.SEMICOLON
        _ = expecting_token and error_if_not_value(tokens, expecting_token)


def external_declaration(tokens, symbol_table):
    #storage_class_specifier? type_specifier init_declarator_list (';' or compound_statement)
    for decl in declarations(tokens, symbol_table):
        _ = decl and isinstance(decl.storage_class, (Auto, Register)) and raise_error(
            '{l} declarations at file scope may not have {s} storage class'.format(l=loc(decl), s=decl.storage_class)
        )
        yield decl


def translation_unit(tokens, symbol_table):  #: (external_declaration)*
    return chain.from_iterable(imap(external_declaration, takewhile(peek, repeat(tokens)), repeat(symbol_table)))