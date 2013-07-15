__author__ = 'samyvilar'

from collections import defaultdict, OrderedDict

from sequences import peek, consume
from front_end.loader.locations import loc, EOFLocation
from front_end.tokenizer.tokens import TOKENS, IDENTIFIER

from front_end.parser.ast.expressions import exp

from front_end.parser.types import CType, FunctionType, PointerType, set_core_type, c_type, StructType, ArrayType
from front_end.parser.types import VoidType, CharType, ShortType, IntegerType, LongType, FloatType, DoubleType
from front_end.parser.types import IntegralType
from front_end.parser.ast.declarations import AbstractDeclarator, Declarator, name
from front_end.parser.ast.declarations import Auto, Extern, Static, Register

from front_end.errors import error_if_not_value, error_if_not_type


def parse_array_dimensions(tokens, symbol_table):
    from front_end.parser.expressions.expression import constant_expression  # No choice expression uses type_name
    location = EOFLocation

    def dimensions(tokens):
        while peek(tokens, default='') == TOKENS.LEFT_BRACKET:
            location = loc(consume(tokens))
            const_exp = constant_expression(tokens, symbol_table)
            _ = error_if_not_value(tokens, TOKENS.RIGHT_BRACKET)
            _ = error_if_not_type([c_type(const_exp)], IntegralType)
            if exp(const_exp) < 0:
                raise ValueError('{l} array size is negative'.format(l=loc(const_exp)))
            yield exp(const_exp), location

    dims = dimensions(tokens)
    dec_array_type = ctype = ArrayType(CType(location), *next(dims))
    for length, location in dims:
        dec_array_type.c_type = ArrayType(CType(location), length, location)
        dec_array_type = dec_array_type.c_type
    return ctype


def parameter_declaration(tokens, symbol_table):  # : type_specifier (declarator | abstract_declarator)*
    base_type = type_specifier(tokens, symbol_table)

    if peek(tokens, default='') in {TOKENS.STAR, TOKENS.LEFT_PARENTHESIS, TOKENS.LEFT_BRACKET} or \
       isinstance(peek(tokens, default=''), IDENTIFIER):
        c_decl = abstract_declarator(tokens, symbol_table)
        set_core_type(c_decl, base_type)
        return c_decl

    return AbstractDeclarator(base_type, loc(base_type))


def parameter_type_list(tokens, symbol_table):  # : parameter_declaration (',' parameter_declaration)*
    yield parameter_declaration(tokens, symbol_table)
    while peek(tokens, default='') == TOKENS.COMMA:
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
    if isinstance(peek(tokens, default=''), IDENTIFIER):
        ident = consume(tokens)
        dec = Declarator(ident, CType(loc(ident)), None, loc(ident))
    elif peek(tokens, default='') == TOKENS.LEFT_PARENTHESIS:
        _ = consume(tokens)
        dec = declarator(tokens, symbol_table)
        _ = error_if_not_value(tokens, TOKENS.RIGHT_PARENTHESIS)
    else:
        raise ValueError('{l} direct_declarator expected an IDENTIFIER or ( got {got}.'.format(
            l=loc(peek(tokens, default=EOFLocation)), got=peek(tokens, default='')
        ))

    if peek(tokens, default='') == TOKENS.LEFT_PARENTHESIS:
        location = loc(consume(tokens))
        parameter_types_decl = []
        if peek(tokens, default='') != TOKENS.RIGHT_PARENTHESIS:
            parameter_types_decl = list(parameter_type_list(tokens, symbol_table))
        _ = error_if_not_value(tokens, TOKENS.RIGHT_PARENTHESIS)
        set_core_type(dec, FunctionType(CType(location), parameter_types_decl, location))
    elif peek(tokens, default='') == TOKENS.LEFT_BRACKET:
        set_core_type(dec, parse_array_dimensions(tokens, symbol_table))
    return dec


def declarator(tokens, symbol_table):  # : pointer? direct_declarator
    pointer_type = None
    if peek(tokens, default='') == TOKENS.STAR:
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

    if isinstance(peek(tokens, default=''), IDENTIFIER):
        name = consume(tokens)
        c_decl = Declarator(name, CType(loc(name)), None, loc(name))
    elif peek(tokens, default='') == TOKENS.LEFT_PARENTHESIS:
        # TODO There is a subtle ambiguity between abstract_decl and parameter_type_list
        _ = consume(tokens)
        c_decl = abstract_declarator(tokens, symbol_table)
        _ = error_if_not_value(tokens, TOKENS.RIGHT_PARENTHESIS)
    elif peek(tokens, default='') == TOKENS.LEFT_BRACKET:
        c_decl = AbstractDeclarator(parse_array_dimensions(tokens, symbol_table), loc(c_type))
    else:
        raise ValueError('{l} Expected either (, [ or IDENTIFIER got {got}'.format(
            l=loc(peek(tokens, default=EOFLocation)), got=peek(tokens, default='')
        ))

    if peek(tokens, default='') == TOKENS.LEFT_PARENTHESIS:
        location, parameter_types_decl = loc(consume(tokens)), []
        if peek(tokens, default='') != TOKENS.RIGHT_PARENTHESIS:
            parameter_types_decl = list(parameter_type_list(tokens, symbol_table))
        _ = error_if_not_value(tokens, TOKENS.RIGHT_PARENTHESIS)
        set_core_type(c_decl, FunctionType(CType(location), parameter_types_decl, location))
    elif peek(tokens, default='') == TOKENS.LEFT_BRACKET:
        set_core_type(c_decl, parse_array_dimensions(tokens, symbol_table))

    return c_decl


def abstract_declarator(tokens, symbol_table): # pointer direct_abstract_declarator? | direct_abstract_declarator
    if peek(tokens, default='') == TOKENS.STAR:
        pointer_type = pointer(tokens)
        if peek(tokens, default='') in {TOKENS.LEFT_PARENTHESIS, TOKENS.LEFT_BRACKET} or \
           isinstance(peek(tokens, default=''), IDENTIFIER):
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
    while peek(tokens, default='') == TOKENS.STAR:
        location = loc(consume(tokens))
        pointer_type.c_type = PointerType(CType(location), location)
        pointer_type = c_type(pointer_type)
    return initial_pointer


def storage_class_specifier(tokens, symbol_table):
    """ : TYPEDEF | EXTERN | STATIC | AUTO | REGISTER or tokens """
    return peek(tokens, default=None) and storage_class_specifier.rules[peek(tokens)](tokens, symbol_table)
storage_class_specifier.rules = defaultdict(lambda: lambda *_: None)
storage_class_specifier.rules.update({
    TOKENS.EXTERN: lambda tokens, symbol_table: Extern(loc(consume(tokens))),
    TOKENS.STATIC: lambda tokens, symbol_table: Static(loc(consume(tokens))),
    TOKENS.REGISTER: lambda tokens, symbol_table: Register(loc(consume(tokens))),
    TOKENS.AUTO: lambda tokens, symbol_table: Auto(loc(consume(tokens))),
})


def parse_sign_token(tokens, _):
    sign = consume(tokens) == TOKENS.UNSIGNED
    if peek(tokens, default='') not in {TOKENS.CHAR, TOKENS.SHORT, TOKENS.INT, TOKENS.LONG}:
        raise ValueError('{l} Expected either char, short, int, long, got {g}'.format(
            l=loc(peek(tokens, default=EOFLocation), g=peek(tokens, default=''))
        ))
    token = consume(tokens)
    return type_specifier.rules[token](loc(token), unsigned=sign)


def parse_struct_members(tokens, symbol_table):
    location, members = loc(consume(tokens)), OrderedDict()
    while peek(tokens, default='') != TOKENS.RIGHT_BRACE:
        type_spec = type_specifier(tokens, symbol_table)
        while peek(tokens, default='') != TOKENS.SEMICOLON:
            decl = declarator(tokens, symbol_table)
            set_core_type(decl, type_spec)
            if name(decl) in members:
                raise ValueError('{l} Duplicate struct member {name} previous at {at}'.format(
                    l=loc(decl), name=name(decl), at=loc(members[name(decl)])
                ))
            members[name(decl)] = decl
            if peek(tokens, default='') != TOKENS.SEMICOLON:
                _ = error_if_not_value(tokens, TOKENS.COMMA)
        _ = error_if_not_value(tokens, TOKENS.SEMICOLON)
    _ = error_if_not_value(tokens, TOKENS.RIGHT_BRACE)
    return members


def struct_specifier(tokens, symbol_table):
    """
    : 'struct' IDENTIFIER
    | 'struct' IDENTIFIER  '{' (type_specifier declarator ';')* '}'
    | 'struct' '{' (type_specifier declarator ';')* '}'
    """
    location = loc(consume(tokens))
    if peek(tokens, default='') == TOKENS.LEFT_BRACE:  # anonymous structure.
        obj = StructType(None, parse_struct_members(tokens, symbol_table), location)
    elif isinstance(peek(tokens, default=''), IDENTIFIER):
        struct_name = consume(tokens)
        # Structs are bit tricky, since any of its members may contain itself as a reference, so we'll add the type to
        # the symbol table before adding the members ...
        if peek(tokens, default='') == TOKENS.LEFT_BRACE:
            obj = StructType(struct_name, None, loc(struct_name))
            symbol_table[name(obj)] = obj
            obj.members = parse_struct_members(tokens, symbol_table)
        else:  # if struct is incomplete search all frames
            obj = symbol_table[StructType.get_name(struct_name)]
        return obj
    else:
        raise ValueError('{l} Expected IDENTIFIER or "{" got {got}'.format(
            loc=loc(peek(tokens, default=EOFLocation)), got=peek(tokens, default='')
        ))
    return obj


def no_type_specifier(tokens, _):
    raise ValueError('{l} Expected a type_specifier or type_name got {got}'.format(
        l=loc(peek(tokens, default=EOFLocation)), got=peek(tokens, default='')
    ))


def type_specifier(tokens, symbol_table, *args):
    """
        : 'void'
        | ['signed' or 'unsigned'] 'char' | ['signed' or 'unsigned'] 'short'
        | ['signed' or 'unsigned'] 'int' | ['signed' or 'unsigned'] 'long'
        | 'float' | 'double'
        | struct_specifier
        | TYPE_NAME
    """
    if peek(tokens, default='') in type_specifier.rules:
        return type_specifier.rules[peek(tokens)](tokens, symbol_table)
    elif isinstance(symbol_table.get(peek(tokens, default=''), ''), CType):
        return symbol_table[peek(tokens)](loc(consume(tokens)))
    elif args:
        return args[0]
    raise ValueError('{l} Expected type_specifier or TYPE_NAME got {got}'.format(
        l=loc(peek(tokens, default=EOFLocation)), got=peek(tokens, default='')
    ))
type_specifier.rules = defaultdict(lambda: no_type_specifier)
type_specifier.rules.update({
    TOKENS.VOID: lambda tokens, symbol_table: VoidType(loc(consume(tokens))),
    TOKENS.CHAR: lambda tokens, symbol_table: CharType(loc(consume(tokens))),
    TOKENS.SHORT: lambda tokens, symbol_table: ShortType(loc(consume(tokens))),
    TOKENS.INT: lambda tokens, symbol_table: IntegerType(loc(consume(tokens))),
    TOKENS.LONG: lambda tokens, symbol_table: LongType(loc(consume(tokens))),
    TOKENS.FLOAT: lambda tokens, symbol_table: FloatType(loc(consume(tokens))),
    TOKENS.DOUBLE: lambda tokens, symbol_table: DoubleType(loc(consume(tokens))),

    TOKENS.STRUCT: struct_specifier,
    TOKENS.SIGNED: parse_sign_token,
    TOKENS.UNSIGNED: parse_sign_token,
})


def type_name(tokens, symbol_table):  #: type_specifier abstract_declarator?   # returns CType
    base_type = type_specifier(tokens, symbol_table)

    if peek(tokens, default='') in {TOKENS.LEFT_PARENTHESIS, TOKENS.LEFT_BRACKET, TOKENS.STAR} \
       or isinstance(peek(tokens, default=''), IDENTIFIER):
        abs_decl = abstract_declarator(tokens, symbol_table)
        set_core_type(abs_decl, base_type)
        return c_type(abs_decl)

    return base_type