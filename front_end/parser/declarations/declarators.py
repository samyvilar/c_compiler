__author__ = 'samyvilar'

from itertools import chain, repeat, takewhile, imap

from utils.sequences import peek, consume, peek_or_terminal
from utils.rules import rules, set_rules, get_rule, identity
from front_end.loader.locations import loc, EOFLocation
from front_end.tokenizer.tokens import TOKENS, IDENTIFIER

from front_end.parser.ast.expressions import exp
from front_end.parser.ast.declarations import TypeDef

from front_end.parser.types import CType, FunctionType, PointerType, set_core_type, c_type, ArrayType
from front_end.parser.types import IntegralType, VAListType

from front_end.parser.ast.declarations import AbstractDeclarator, Declarator
from front_end.parser.ast.declarations import Auto, Extern, Static, Register

from utils.errors import error_if_not_value, error_if_not_type


def parse_array_dimensions(tokens, symbol_table):
    constant_expression = symbol_table['__ constant_expression __']
    location = EOFLocation

    def dimensions(tokens):
        while peek(tokens) == TOKENS.LEFT_BRACKET:
            location = loc(consume(tokens))
            if peek(tokens) == TOKENS.RIGHT_BRACKET:
                size = None
            else:
                const_exp = constant_expression(tokens, symbol_table)
                _ = error_if_not_type(c_type(const_exp), IntegralType)
                if exp(const_exp) < 0:
                    raise ValueError('{l} array size is negative'.format(l=loc(const_exp)))
                size = exp(const_exp)
            _ = error_if_not_value(tokens, TOKENS.RIGHT_BRACKET)
            yield size, location

    dims = dimensions(tokens)
    dec_array_type = ctype = ArrayType(CType(location), *next(dims))
    for length, location in dims:
        if length is None:
            raise ValueError('{l} only the first array size may be omitted ...'.format(l=location))
        dec_array_type.c_type = ArrayType(CType(location), length, location)
        dec_array_type = dec_array_type.c_type
    return ctype


def ellipsis_parameter_declaration(tokens, symbol_table):
    ellipsis = consume(tokens)
    return Declarator(ellipsis, VAListType(loc(ellipsis)), None, loc(ellipsis))


def default_parameter_declaration(tokens, symbol_table):
    base_type = symbol_table['__ specifier_qualifier_list __'](tokens, symbol_table)
    c_decl = AbstractDeclarator(base_type, loc(base_type))

    token = peek_or_terminal(tokens)
    if token in {TOKENS.STAR, TOKENS.LEFT_PARENTHESIS, TOKENS.LEFT_BRACKET} or isinstance(token, IDENTIFIER):
        c_decl = abstract_declarator(tokens, symbol_table)
        set_core_type(c_decl, base_type)

    return c_decl


def parameter_declaration(tokens, symbol_table):
    # : specifier_qualifier_list (declarator | abstract_declarator) or `...`
    return rules(parameter_declaration)[peek_or_terminal(tokens)](tokens, symbol_table)
set_rules(parameter_declaration, ((TOKENS.ELLIPSIS, ellipsis_parameter_declaration),), default_parameter_declaration)


def parameter_type_list(tokens, symbol_table):  # : parameter_declaration (',' parameter_declaration)*
    return chain(
        (parameter_declaration(tokens, symbol_table),),
        imap(
            parameter_declaration,
            takewhile(lambda tokens: peek(tokens) == TOKENS.COMMA and consume(tokens), repeat(tokens)),
            repeat(symbol_table)
        )
    )


def identifier_direct_declarator(tokens, symbol_table):
    ident = error_if_not_type(consume(tokens), IDENTIFIER)
    return Declarator(ident, CType(loc(ident)), None, loc(ident))


def nested_declarator(tokens, symbol_table):
    dec = error_if_not_value(tokens, TOKENS.LEFT_PARENTHESIS) and symbol_table['__ declarator __'](tokens, symbol_table)
    return error_if_not_value(tokens, TOKENS.RIGHT_PARENTHESIS) and dec


def function_parameter_declarations(tokens, symbol_table):
    location = loc(error_if_not_value(tokens, TOKENS.LEFT_PARENTHESIS))
    parameter_types_decl = tuple(() if peek(tokens, TOKENS.RIGHT_PARENTHESIS) == TOKENS.RIGHT_PARENTHESIS else
                                 parameter_type_list(tokens, symbol_table))
    return error_if_not_value(tokens, TOKENS.RIGHT_PARENTHESIS) and FunctionType(
        CType(location), parameter_types_decl, location
    )


def declarator_suffix(tokens, symbol_table):
    return rules(declarator_suffix)[peek_or_terminal(tokens)](tokens, symbol_table)
set_rules(
    declarator_suffix,
    ((TOKENS.LEFT_PARENTHESIS, function_parameter_declarations), (TOKENS.LEFT_BRACKET, parse_array_dimensions))
)


def direct_declarator(tokens, symbol_table):
    """
        :   (IDENTIFIER | '(' declarator ')') declarator_suffix*

        declarator_suffix
            :   '[' constant_expression ']'
            |   '[' ']'
            |   '(' parameter_type_list ')'
            |   '(' ')'
    """
    dec = get_rule(direct_declarator, peek_or_terminal(tokens), hash_funcs=(type, identity))(tokens, symbol_table)
    _ = peek_or_terminal(tokens) in rules(declarator_suffix) and set_core_type(
        dec, declarator_suffix(tokens, symbol_table))
    return dec
set_rules(
    direct_declarator, ((IDENTIFIER, identifier_direct_declarator), (TOKENS.LEFT_PARENTHESIS, nested_declarator))
)


def pointer_type_declarator(tokens, symbol_table):
    pointer_type = pointer(tokens, symbol_table)
    return set_core_type(direct_declarator(tokens, symbol_table), pointer_type)


def declarator(tokens, symbol_table):  # : pointer? direct_declarator
    return rules(declarator)[peek_or_terminal(tokens)](tokens, symbol_table)
set_rules(declarator, ((TOKENS.STAR, pointer_type_declarator),), direct_declarator)


def abstract_array_type_declarator(tokens, symbol_table):
    return AbstractDeclarator(parse_array_dimensions(tokens, symbol_table), loc(peek_or_terminal(tokens)))


def nested_abstract_declarator(tokens, symbol_table):
    _ = error_if_not_value(tokens, TOKENS.LEFT_PARENTHESIS)
    dec = abstract_declarator(tokens, symbol_table)
    return error_if_not_value(tokens, TOKENS.RIGHT_PARENTHESIS) and dec


def direct_abstract_declarator(tokens, symbol_table):
    """
        :( IDENTIFIER | '(' abstract_declarator ')' | abstract_declarator_suffix ) abstract_declarator_suffix*

            abstract_declarator_suffix
                :	'[' ']'
                |   '[' constant_expression ']'
                |	'(' ')'
                |	'(' parameter_type_list ')'
    """

    decl = get_rule(direct_abstract_declarator, peek_or_terminal(tokens), hash_funcs=(type, identity))(
        tokens, symbol_table
    )
    _ = peek_or_terminal(tokens) in rules(declarator_suffix) and set_core_type(
        decl, declarator_suffix(tokens, symbol_table))
    return decl
set_rules(
    direct_abstract_declarator,
    (
        (IDENTIFIER, identifier_direct_declarator),
        (TOKENS.LEFT_BRACKET, abstract_array_type_declarator),
        (TOKENS.LEFT_PARENTHESIS, nested_abstract_declarator)
    )
)


def pointer_type_abstract_declarator(tokens, symbol_table):
    decl = AbstractDeclarator(pointer(tokens, symbol_table), loc(peek_or_terminal(tokens)))
    if get_rule(direct_abstract_declarator, peek_or_terminal(tokens), None, hash_funcs=(type, identity)) is not None:
        decl = set_core_type(direct_abstract_declarator(tokens, symbol_table), c_type(decl))
    return decl


def abstract_declarator(tokens, symbol_table):  # pointer direct_abstract_declarator? | direct_abstract_declarator
    return rules(abstract_declarator)[peek_or_terminal(tokens)](tokens, symbol_table)
set_rules(abstract_declarator, ((TOKENS.STAR, pointer_type_abstract_declarator),), direct_abstract_declarator)


def pointer(tokens, symbol_table):  # parse a list of **1** or or more pointers
    location = loc(error_if_not_value(tokens, TOKENS.STAR))
    const, volatile = symbol_table['__ type_qualifiers __'](tokens, symbol_table, (False, False))
    pointer_type = PointerType(pointer_or_ctype(tokens, symbol_table), location=location)
    pointer_type.const, pointer_type.volatile = const, volatile
    return pointer_type


def pointer_or_ctype(tokens, symbol_table):
    return rules(pointer_or_ctype)[peek_or_terminal(tokens)](tokens, symbol_table)
set_rules(pointer_or_ctype, ((TOKENS.STAR, pointer),), lambda tokens, *args: CType(loc(peek_or_terminal(tokens))))


def storage_class_specifier(tokens, symbol_table):
    """ : TYPEDEF | EXTERN | STATIC | AUTO | REGISTER or None """
    return rules(storage_class_specifier)[peek_or_terminal(tokens)](tokens, symbol_table)
set_rules(
    storage_class_specifier,
    (
        (TOKENS.EXTERN, lambda tokens, symbol_table:    Extern(loc(consume(tokens)))),
        (TOKENS.STATIC, lambda tokens, symbol_table:    Static(loc(consume(tokens)))),
        (TOKENS.REGISTER, lambda tokens, symbol_table:  Register(loc(consume(tokens)))),
        (TOKENS.AUTO, lambda tokens, symbol_table:      Auto(loc(consume(tokens)))),
        (TOKENS.TYPEDEF, lambda tokens, symbol_table:   TypeDef('', '', loc(consume(tokens))))
    ),
    lambda tokens, symbol_table: None,
)

