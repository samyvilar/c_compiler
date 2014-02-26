__author__ = 'samyvilar'

from collections import OrderedDict
from itertools import imap

from utils.sequences import peek, consume, peek_or_terminal, takewhile
from utils.rules import rules, set_rules

from front_end.loader.locations import loc, EOFLocation
from front_end.tokenizer.tokens import TOKENS, IDENTIFIER

from front_end.parser.ast.declarations import name, Definition
from front_end.parser.ast.expressions import ConstantExpression, exp

from front_end.parser.types import set_core_type, c_type, IntegerType, EnumType, UnionType, StructType, CType
from front_end.parser.types import VoidType, CharType, ShortType, LongType, FloatType, DoubleType, no_default

from utils.errors import error_if_not_value, error_if_not_type


def parse_sign_token(tokens, symbol_table):
    sign = consume(tokens) == TOKENS.UNSIGNED
    base_type = specifier_qualifier_list(tokens, symbol_table)
    base_type.unsigned = sign
    return base_type


def parse_struct_members(tokens, symbol_table):
    declarator = symbol_table['__ declarator __']
    location, members = loc(consume(tokens)), OrderedDict()
    while peek(tokens, TOKENS.RIGHT_BRACE) != TOKENS.RIGHT_BRACE:
        type_spec = specifier_qualifier_list(tokens, symbol_table)
        while peek(tokens, TOKENS.SEMICOLON) != TOKENS.SEMICOLON:
            decl = declarator(tokens, symbol_table)
            set_core_type(decl, type_spec)
            if name(decl) in members:
                raise ValueError('{l} Duplicate struct member {name} previous at {at}'.format(
                    l=loc(decl), name=name(decl), at=loc(members[name(decl)])
                ))
            members[name(decl)] = decl
            _ = peek_or_terminal(tokens) != TOKENS.SEMICOLON and error_if_not_value(tokens, TOKENS.COMMA)
        _ = error_if_not_value(tokens, TOKENS.SEMICOLON)
    _ = error_if_not_value(tokens, TOKENS.RIGHT_BRACE)
    return members


def parse_enum_members(tokens, symbol_table):
    constant_expression = symbol_table['__ constant_expression __']
    location, members, current_value = loc(consume(tokens)), OrderedDict(), 0

    while peek(tokens, TOKENS.RIGHT_BRACE) != TOKENS.RIGHT_BRACE:
        ident = error_if_not_type(consume(tokens, ''), IDENTIFIER)
        value = ConstantExpression(current_value, IntegerType(location), location)
        if peek_or_terminal(tokens) == TOKENS.EQUAL and consume(tokens):
            value = constant_expression(tokens, symbol_table)
            _ = error_if_not_type(c_type(value), IntegerType)
        current_value = error_if_not_type(exp(value), (int, long))

        symbol_table[ident] = value  # Add value to symbol_table
        members[ident] = Definition(ident, c_type(value), value, location)

        _ = peek_or_terminal(tokens) == TOKENS.COMMA and consume(tokens)
    _ = error_if_not_value(tokens, TOKENS.RIGHT_BRACE)

    return members


def composite_specifier(
        tokens,
        symbol_table,
        obj_type=StructType,
        member_parse_func=parse_struct_members,
        terminal=object()
):
    """
    : 'composite type' IDENTIFIER
    | 'composite type' IDENTIFIER  '{' members '}'
    | 'composite type' '{' members '}'
    """
    location = loc(consume(tokens))
    if peek_or_terminal(tokens) == TOKENS.LEFT_BRACE:  # anonymous composite ...
        return obj_type(None, member_parse_func(tokens, symbol_table), location)

    if isinstance(peek_or_terminal(tokens), IDENTIFIER):
        obj = symbol_table.get(obj_type.get_name(peek(tokens)), obj_type(consume(tokens), None, location))
        # some composites are bit tricky such as Struct/Union ...
        # since any of its members may contain itself as a reference, so we'll add the type to
        # the symbol table before adding the members ...
        # TODO: make types immutable, right now they are being shared.
        if symbol_table.get(obj.name, terminal) is terminal:
            symbol_table[name(obj)] = obj
        if peek_or_terminal(tokens) == TOKENS.LEFT_BRACE:
            obj.members = member_parse_func(tokens, symbol_table)

        return obj

    raise ValueError('{l} Expected IDENTIFIER or LEFT_BRACE got {got}'.format(
        l=loc(peek(tokens, EOFLocation)), got=peek(tokens, '')
    ))


def no_type_specifier(tokens, _):
    raise ValueError('{l} Expected a type_specifier or type_name got {got}'.format(
        l=loc(peek(tokens, EOFLocation)), got=peek(tokens, '')
    ))


def _long(tokens, symbol_table):
    location = loc(consume(tokens))
    return LongType(type_specifier(tokens, symbol_table, IntegerType(location)), location)


def _short(tokens, symbol_table):
    location = loc(consume(tokens))
    return ShortType(type_specifier(tokens, symbol_table, IntegerType(location)), location)


def type_specifier(tokens, symbol_table, default=no_default):
    """
        : 'void'
        | ['signed' | 'unsigned'] 'char' | ['signed' | 'unsigned'] 'short'
        | ['signed' | 'unsigned'] 'int' | ['signed' | 'unsigned'] 'long'
        | 'float' | 'double'
        | struct_specifier
        | union_specifier
        | enum_specifier
        | TYPE_NAME
    """
    token = peek_or_terminal(tokens)
    if token in rules(type_specifier):
        return rules(type_specifier)[token](tokens, symbol_table)
    elif isinstance(symbol_table.get(token, token), CType):
        return symbol_table[token](loc(consume(tokens)))
    elif default is not no_default:
        return default
    raise ValueError('{l} Expected type_specifier or TYPE_NAME got {got}'.format(
        l=loc(peek(tokens, EOFLocation)), got=peek(tokens, '')
    ))
set_rules(
    type_specifier,
    {
        TOKENS.VOID: lambda tokens, symbol_table: VoidType(loc(consume(tokens))),
        TOKENS.CHAR: lambda tokens, symbol_table: CharType(loc(consume(tokens))),
        TOKENS.INT: lambda tokens, symbol_table: IntegerType(loc(consume(tokens))),
        TOKENS.FLOAT: lambda tokens, symbol_table: FloatType(loc(consume(tokens))),
        TOKENS.DOUBLE: lambda tokens, symbol_table: DoubleType(loc(consume(tokens))),

        TOKENS.LONG: _long,
        TOKENS.SHORT: _short,

        TOKENS.SIGNED: parse_sign_token,
        TOKENS.UNSIGNED: parse_sign_token,

        TOKENS.STRUCT: composite_specifier,
        TOKENS.UNION: lambda tokens, symbol_table: composite_specifier(
            tokens, symbol_table, obj_type=UnionType),
        TOKENS.ENUM: lambda tokens, symbol_table: composite_specifier(
            tokens, symbol_table, obj_type=EnumType, member_parse_func=parse_enum_members
        ),
    },
    no_type_specifier

)


def type_qualifiers(tokens, _, defaults=None):  # : ('const' or volatile or *args)*
    values = set(takewhile(rules(type_qualifiers).__contains__, tokens))
    const, volatile = imap(values.__contains__, (TOKENS.CONST, TOKENS.VOLATILE))
    if not values and not defaults:
        raise ValueError('{l} Expected TOKENS.CONST or TOKEN.VOLATILE got {g}'.format(
            l=loc(peek(tokens, EOFLocation)), g=peek(tokens, '')
        ))
    return const or defaults[0], volatile or defaults[1]
set_rules(type_qualifiers, {TOKENS.VOLATILE, TOKENS.CONST})


def specifier_qualifier_list(tokens, symbol_table):
    const, volatile = type_qualifiers(tokens, symbol_table, (False, False))
    base_type = type_specifier(tokens, symbol_table, IntegerType(loc(peek(tokens, EOFLocation))))
    base_type.const, base_type.volatile = type_qualifiers(tokens, symbol_table, (const, volatile))
    return base_type
set_rules(specifier_qualifier_list, set(rules(type_qualifiers)) | set(rules(type_specifier)))


def type_name(tokens, symbol_table):  #: type_specifier abstract_declarator?   # returns CType
    base_type = specifier_qualifier_list(tokens, symbol_table)
    abstract_declarator = symbol_table['__ abstract_declarator __']
    if peek_or_terminal(tokens) in {TOKENS.LEFT_PARENTHESIS, TOKENS.LEFT_BRACKET, TOKENS.STAR} \
       or isinstance(peek_or_terminal(tokens), IDENTIFIER):
        abs_decl = abstract_declarator(tokens, symbol_table)
        set_core_type(abs_decl, base_type)
        return c_type(abs_decl)

    return base_type
set_rules(type_name, set(rules(specifier_qualifier_list)))


def is_type_name(token, symbol_table):
    return token in rules(type_name) or isinstance(symbol_table.get(token, token), CType)
