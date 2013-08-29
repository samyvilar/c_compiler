__author__ = 'samyvilar'

from collections import defaultdict, OrderedDict

from sequences import peek, consume
from front_end.loader.locations import loc, EOFLocation
from front_end.tokenizer.tokens import TOKENS, IDENTIFIER

from front_end.parser.ast.expressions import exp
from front_end.parser.ast.declarations import TypeDef

from front_end.parser.types import CType, FunctionType, PointerType, set_core_type, c_type, StructType, ArrayType
from front_end.parser.types import VoidType, CharType, ShortType, IntegerType, LongType, FloatType, DoubleType
from front_end.parser.types import IntegralType, UnionType, VAListType

from front_end.parser.ast.declarations import AbstractDeclarator, Declarator, name
from front_end.parser.ast.declarations import Auto, Extern, Static, Register

from front_end.errors import error_if_not_value, error_if_not_type


def parse_array_dimensions(tokens, symbol_table):
    from front_end.parser.expressions.expression import constant_expression  # No choice expression uses type_name
    location = EOFLocation

    def dimensions(tokens):
        while peek(tokens) == TOKENS.LEFT_BRACKET:
            location = loc(consume(tokens))
            const_exp = constant_expression(tokens, symbol_table)
            _ = error_if_not_value(tokens, TOKENS.RIGHT_BRACKET)
            _ = error_if_not_type(c_type(const_exp), IntegralType)
            if exp(const_exp) < 0:
                raise ValueError('{l} array size is negative'.format(l=loc(const_exp)))
            yield exp(const_exp), location

    dims = dimensions(tokens)
    dec_array_type = ctype = ArrayType(CType(location), *next(dims))
    for length, location in dims:
        dec_array_type.c_type = ArrayType(CType(location), length, location)
        dec_array_type = dec_array_type.c_type
    return ctype


def parameter_declaration(tokens, symbol_table):
    # : specifier_qualifier_list (declarator | abstract_declarator) or `...`
    if peek(tokens, '') == TOKENS.ELLIPSIS:
        ellipsis = consume(tokens)
        return Declarator(ellipsis, VAListType(loc(ellipsis)), None, loc(ellipsis))

    base_type = specifier_qualifier_list(tokens, symbol_table)

    if peek(tokens, '') in {TOKENS.STAR, TOKENS.LEFT_PARENTHESIS, TOKENS.LEFT_BRACKET} or \
       isinstance(peek(tokens, ''), IDENTIFIER):
        c_decl = abstract_declarator(tokens, symbol_table)
        set_core_type(c_decl, base_type)
        return c_decl

    return AbstractDeclarator(base_type, loc(base_type))


def parameter_type_list(tokens, symbol_table):  # : parameter_declaration (',' parameter_declaration)*
    yield parameter_declaration(tokens, symbol_table)
    while peek(tokens) == TOKENS.COMMA:
        _ = consume(tokens)
        yield parameter_declaration(tokens, symbol_table)


def direct_declarator(tokens, symbol_table):
    """
        :   (IDENTIFIER | '(' declarator ')') declarator_suffix*

        declarator_suffix
            :   '[' constant_expression ']'
            |   '(' parameter_type_list ')'
            |   '(' ')'
    """
    if isinstance(peek(tokens, ''), IDENTIFIER):
        ident = consume(tokens)
        dec = Declarator(ident, CType(loc(ident)), None, loc(ident))
    elif peek(tokens, '') == TOKENS.LEFT_PARENTHESIS:
        _ = consume(tokens)
        dec = declarator(tokens, symbol_table)
        _ = error_if_not_value(tokens, TOKENS.RIGHT_PARENTHESIS)
    else:
        raise ValueError('{l} direct_declarator expected an IDENTIFIER or ( got {got}.'.format(
            l=loc(peek(tokens, EOFLocation)), got=peek(tokens, '')
        ))

    if peek(tokens, '') == TOKENS.LEFT_PARENTHESIS:
        location = loc(consume(tokens))
        parameter_types_decl = []
        if peek(tokens, '') != TOKENS.RIGHT_PARENTHESIS:
            parameter_types_decl = list(parameter_type_list(tokens, symbol_table))
        _ = error_if_not_value(tokens, TOKENS.RIGHT_PARENTHESIS)
        set_core_type(dec, FunctionType(CType(location), parameter_types_decl, location))
    elif peek(tokens, '') == TOKENS.LEFT_BRACKET:
        set_core_type(dec, parse_array_dimensions(tokens, symbol_table))
    return dec


def declarator(tokens, symbol_table):  # : pointer? direct_declarator
    pointer_type = None
    if peek(tokens, '') == TOKENS.STAR:
        pointer_type = pointer(tokens)

    dir_decl = direct_declarator(tokens, symbol_table)
    if isinstance(pointer_type, PointerType):
        set_core_type(dir_decl, pointer_type)

    return dir_decl


def direct_abstract_declarator(tokens, symbol_table):
    """
        :( IDENTIFIER | '(' abstract_declarator ')' | abstract_declarator_suffix ) abstract_declarator_suffix*

            abstract_declarator_suffix
                :	'[' constant_expression ']'
                |	'(' ')'
                |	'(' parameter_type_list ')'
    """

    if isinstance(peek(tokens, ''), IDENTIFIER):
        name = consume(tokens)
        c_decl = Declarator(name, CType(loc(name)), None, loc(name))
    elif peek(tokens, '') == TOKENS.LEFT_PARENTHESIS:
        # TODO There is a subtle ambiguity between abstract_decl and parameter_type_list
        _ = consume(tokens)
        c_decl = abstract_declarator(tokens, symbol_table)
        _ = error_if_not_value(tokens, TOKENS.RIGHT_PARENTHESIS)
    elif peek(tokens, '') == TOKENS.LEFT_BRACKET:
        c_decl = AbstractDeclarator(parse_array_dimensions(tokens, symbol_table), loc(c_type))
    else:
        raise ValueError('{l} Expected either (, [ or IDENTIFIER got {got}'.format(
            l=loc(peek(tokens, EOFLocation)), got=peek(tokens, '')
        ))

    if peek(tokens, '') == TOKENS.LEFT_PARENTHESIS:
        location, parameter_types_decl = loc(consume(tokens)), []
        if peek(tokens, '') != TOKENS.RIGHT_PARENTHESIS:
            parameter_types_decl = list(parameter_type_list(tokens, symbol_table))
        _ = error_if_not_value(tokens, TOKENS.RIGHT_PARENTHESIS)
        set_core_type(c_decl, FunctionType(CType(location), parameter_types_decl, location))
    elif peek(tokens, '') == TOKENS.LEFT_BRACKET:
        set_core_type(c_decl, parse_array_dimensions(tokens, symbol_table))

    return c_decl


def abstract_declarator(tokens, symbol_table): # pointer direct_abstract_declarator? | direct_abstract_declarator
    if peek(tokens, '') == TOKENS.STAR:
        pointer_type = pointer(tokens)
        if peek(tokens, '') in {TOKENS.LEFT_PARENTHESIS, TOKENS.LEFT_BRACKET} or \
           isinstance(peek(tokens, ''), IDENTIFIER):
            c_decl = direct_abstract_declarator(tokens, symbol_table)
            set_core_type(c_decl, pointer_type)
        else:
            c_decl = AbstractDeclarator(pointer_type, loc(pointer_type))
    else:
        c_decl = direct_abstract_declarator(tokens, symbol_table)
    return c_decl


def pointer(tokens):  # parse a list of **1** or or more pointers
    location = loc(consume(tokens))
    initial_pointer = pointer_type = PointerType(CType(location), location)
    initial_pointer.const, initial_pointer.volatile = type_qualifiers(tokens, {}, (False, False))
    while peek(tokens, '') == TOKENS.STAR:
        location = loc(consume(tokens))
        pointer_type.c_type = PointerType(CType(location), location)
        pointer_type = c_type(pointer_type)
        pointer_type.const, pointer_type.volatile = type_qualifiers(tokens, {}, (False, False))
    return initial_pointer


def storage_class_specifier(tokens, symbol_table):
    """ : TYPEDEF | EXTERN | STATIC | AUTO | REGISTER or tokens """
    return peek(tokens, '') and storage_class_specifier.rules[peek(tokens)](tokens, symbol_table)
storage_class_specifier.rules = defaultdict(lambda: lambda *_: None)
storage_class_specifier.rules.update({
    TOKENS.EXTERN: lambda tokens, symbol_table: Extern(loc(consume(tokens))),
    TOKENS.STATIC: lambda tokens, symbol_table: Static(loc(consume(tokens))),
    TOKENS.REGISTER: lambda tokens, symbol_table: Register(loc(consume(tokens))),
    TOKENS.AUTO: lambda tokens, symbol_table: Auto(loc(consume(tokens))),
    TOKENS.TYPEDEF: lambda tokens, symbol_table: TypeDef('', '', loc(consume(tokens)))
})


def parse_sign_token(tokens, symbol_table):
    sign = consume(tokens) == TOKENS.UNSIGNED
    base_type = specifier_qualifier_list(tokens, symbol_table)
    base_type.unsigned = sign
    return base_type


def parse_struct_members(tokens, symbol_table):
    location, members = loc(consume(tokens)), OrderedDict()
    while peek(tokens, '') != TOKENS.RIGHT_BRACE:

        type_spec = specifier_qualifier_list(tokens, symbol_table)

        while peek(tokens, '') != TOKENS.SEMICOLON:
            decl = declarator(tokens, symbol_table)
            set_core_type(decl, type_spec)
            if name(decl) in members:
                raise ValueError('{l} Duplicate struct member {name} previous at {at}'.format(
                    l=loc(decl), name=name(decl), at=loc(members[name(decl)])
                ))
            members[name(decl)] = decl
            if peek(tokens, '') != TOKENS.SEMICOLON:
                _ = error_if_not_value(tokens, TOKENS.COMMA)
        _ = error_if_not_value(tokens, TOKENS.SEMICOLON)
    _ = error_if_not_value(tokens, TOKENS.RIGHT_BRACE)
    return members


def struct_specifier(tokens, symbol_table, obj_type=StructType):
    """
    : 'struct' IDENTIFIER
    | 'struct' IDENTIFIER  '{' (specifier_qualifier_list  declarator ';')* '}'
    | 'struct' '{' (specifier_qualifier_list declarator ';')* '}'
    """
    location = loc(consume(tokens))
    if peek(tokens, '') == TOKENS.LEFT_BRACE:  # anonymous structure.
        obj = obj_type(None, parse_struct_members(tokens, symbol_table), location)
    elif isinstance(peek(tokens, ''), IDENTIFIER):
        obj = symbol_table.get(obj_type.get_name(peek(tokens)), obj_type(consume(tokens), None, location))
        # Structs are bit tricky, since any of its members may contain itself as a reference, so we'll add the type to
        # the symbol table before adding the members ...
        # TODO: make structures types immutable, right now they are being shared.
        terminal = object()
        if symbol_table.get(obj.name, terminal) is terminal:
            symbol_table[name(obj)] = obj
        if peek(tokens, '') == TOKENS.LEFT_BRACE:
            obj.members = parse_struct_members(tokens, symbol_table)

        return obj
    else:
        raise ValueError('{l} Expected IDENTIFIER or "{" got {got}'.format(
            loc=loc(peek(tokens, EOFLocation)), got=peek(tokens, '')
        ))
    return obj


def union_specifier(tokens, symbol_table):
    return struct_specifier(tokens, symbol_table, obj_type=UnionType)


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


def type_specifier(tokens, symbol_table, *args):
    """
        : 'void'
        | ['signed' or 'unsigned'] 'char' | ['signed' or 'unsigned'] 'short'
        | ['signed' or 'unsigned'] 'int' | ['signed' or 'unsigned'] 'long'
        | 'float' | 'double'
        | struct_specifier
        | TYPE_NAME
    """
    if peek(tokens, '') in type_specifier.rules:
        return type_specifier.rules[peek(tokens)](tokens, symbol_table)
    elif isinstance(symbol_table.get(peek(tokens, ''), ''), CType):
        return symbol_table[peek(tokens)](loc(consume(tokens)))
    elif args:
        return args[0]
    raise ValueError('{l} Expected type_specifier or TYPE_NAME got {got}'.format(
        l=loc(peek(tokens, EOFLocation)), got=peek(tokens, default='')
    ))
type_specifier.rules = defaultdict(lambda: no_type_specifier)
type_specifier.rules.update({
    TOKENS.VOID: lambda tokens, symbol_table: VoidType(loc(consume(tokens))),
    TOKENS.CHAR: lambda tokens, symbol_table: CharType(loc(consume(tokens))),
    TOKENS.INT: lambda tokens, symbol_table: IntegerType(loc(consume(tokens))),
    TOKENS.FLOAT: lambda tokens, symbol_table: FloatType(loc(consume(tokens))),
    TOKENS.DOUBLE: lambda tokens, symbol_table: DoubleType(loc(consume(tokens))),

    TOKENS.LONG: _long,
    TOKENS.SHORT: _short,

    TOKENS.STRUCT: struct_specifier,
    TOKENS.SIGNED: parse_sign_token,
    TOKENS.UNSIGNED: parse_sign_token,

    TOKENS.UNION: union_specifier,
})


def type_qualifiers(tokens, _, *args):
    """
        : ('const' or volatile or *args)*
    """
    volatile, const = None, None
    if peek(tokens, '') in {TOKENS.CONST, TOKENS.VOLATILE}:
        while peek(tokens, '') in {TOKENS.CONST, TOKENS.VOLATILE}:
            if peek(tokens) == TOKENS.CONST:
                const = consume(tokens)
            if peek(tokens) == TOKENS.VOLATILE:
                volatile = consume(tokens)
        return const, volatile
    elif args:
        return args[0]
    else:
        raise ValueError('{l} Expected const or volatile got {g}'.format(
            l=loc(peek(tokens, EOFLocation)), g=peek(tokens, '')
        ))
type_qualifiers.rules = {TOKENS.VOLATILE, TOKENS.CONST}


def specifier_qualifier_list(tokens, symbol_table):
    const, volatile = type_qualifiers(tokens, symbol_table, (False, False))
    base_type = type_specifier(tokens, symbol_table, IntegerType(loc(peek(tokens, EOFLocation))))
    base_type.const, base_type.volatile = type_qualifiers(tokens, symbol_table, (const, volatile))
    return base_type
specifier_qualifier_list.rules = type_qualifiers.rules | set(type_specifier.rules.iterkeys())


def type_name(tokens, symbol_table):  #: type_specifier abstract_declarator?   # returns CType
    base_type = specifier_qualifier_list(tokens, symbol_table)

    if peek(tokens, '') in {TOKENS.LEFT_PARENTHESIS, TOKENS.LEFT_BRACKET, TOKENS.STAR} \
       or isinstance(peek(tokens, ''), IDENTIFIER):
        abs_decl = abstract_declarator(tokens, symbol_table)
        set_core_type(abs_decl, base_type)
        return c_type(abs_decl)

    return base_type
type_name.rules = specifier_qualifier_list.rules


def is_type_name(token, symbol_table):
    return token in type_name.rules or isinstance(symbol_table.get(token, ''), CType)