__author__ = 'samyvilar'

from collections import defaultdict, OrderedDict

from front_end.loader.locations import loc
from front_end.tokenizer.tokens import TOKENS, IDENTIFIER

from front_end.parser.ast.expressions import exp

from front_end.parser.types import CType, FunctionType, PointerType, set_core_type, c_type, StructType, ArrayType
from front_end.parser.types import IntegralType
from front_end.parser.ast.declarations import AbstractDeclarator, Declarator, name
from front_end.parser.ast.declarations import Auto, Extern, Static, Register

from front_end.errors import error_if_not_value, error_if_not_any_value, error_if_not_type


def parse_array_dimensions(tokens, symbol_table):
    from front_end.parser.expressions.expression import constant_expression  # No choice expression uses type_name
    location, array_dims = '', []
    while tokens and tokens[0] == TOKENS.LEFT_BRACKET:
        location = loc(tokens.pop(0))
        const_exp = constant_expression(tokens, symbol_table)
        _, _ = error_if_not_value(tokens, TOKENS.RIGHT_BRACKET), error_if_not_type([c_type(const_exp)], IntegralType)
        if exp(const_exp) < 0:
            raise ValueError('{l} array size is negative'.format(l=loc(const_exp)))
        length = exp(const_exp)
        array_dims.append((length, location))

    dec_array_type = ctype = ArrayType(CType(location), *array_dims.pop(0))
    for length, location in array_dims:
        dec_array_type.c_type = ArrayType(CType(location), length, location)
        dec_array_type = dec_array_type.c_type
    return ctype


def parameter_declaration(tokens, symbol_table):  # : type_specifier (declarator | abstract_declarator)*
    base_type = type_specifier(tokens, symbol_table)

    if tokens and \
       (tokens[0] in {TOKENS.STAR, TOKENS.LEFT_PARENTHESIS, TOKENS.LEFT_BRACKET} or isinstance(tokens[0], IDENTIFIER)):
        c_decl = abstract_declarator(tokens, symbol_table)
        set_core_type(c_decl, base_type)
        return c_decl

    return AbstractDeclarator(base_type, loc(base_type))


def parameter_type_list(tokens, symbol_table):  # : parameter_declaration (',' parameter_declaration)*
    parm_list = [parameter_declaration(tokens, symbol_table)]

    while tokens and tokens[0] == TOKENS.COMMA:
        _ = tokens.pop(0)
        parm_list.append(parameter_declaration(tokens, symbol_table))
    return parm_list


def direct_declarator(tokens, symbol_table):
    """
        :   (IDENTIFIER | '(' declarator ')') declarator_suffix*

        declarator_suffix
            :   '[' constant_expression ']'
            |   '(' parameter_type_list ')'
            |   '(' ')'
    """
    if tokens and isinstance(tokens[0], IDENTIFIER):
        ident = tokens.pop(0)
        dec = Declarator(ident, CType(loc(ident)), None, loc(ident))
    elif tokens and tokens[0] == TOKENS.LEFT_PARENTHESIS:
        _ = tokens.pop(0)
        dec = declarator(tokens, symbol_table)
        _ = error_if_not_value(tokens, TOKENS.RIGHT_PARENTHESIS)
    else:
        raise ValueError('{l} direct_declarator expected an identifier or ( got {got}.'.format(
            l=tokens and loc(tokens[0]), got=tokens and tokens[0]
        ))

    if tokens and tokens[0] == TOKENS.LEFT_PARENTHESIS:
        location = loc(tokens.pop(0))
        if tokens and tokens[0] == TOKENS.RIGHT_PARENTHESIS:
            _, parameter_types_decl = tokens.pop(0), []
        elif tokens:
            parameter_types_decl = parameter_type_list(tokens, symbol_table)
            _ = error_if_not_value(tokens, TOKENS.RIGHT_PARENTHESIS)
        else:
            raise ValueError('Expected parameter list or ) got []')
        set_core_type(dec, FunctionType(CType(location), parameter_types_decl, location))
    elif tokens and tokens[0] == TOKENS.LEFT_BRACKET:
        set_core_type(dec, parse_array_dimensions(tokens, symbol_table))
    return dec


def declarator(tokens, symbol_table):  # : pointer? direct_declarator
    pointer_type = None
    if tokens and tokens[0] == TOKENS.STAR:
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

    if tokens and isinstance(tokens[0], IDENTIFIER):
        name = tokens.pop(0)
        c_decl = Declarator(name, CType(loc(name)), None, loc(name))
    elif tokens and tokens[0] == TOKENS.LEFT_PARENTHESIS:
        # TODO There is a subtle ambiguity between abstract_decl and parameter_type_list
        _ = tokens.pop(0)
        c_decl = abstract_declarator(tokens, symbol_table)
        _ = error_if_not_value(tokens, TOKENS.RIGHT_PARENTHESIS)
    elif tokens and tokens[0] == TOKENS.LEFT_BRACKET:
        c_decl = AbstractDeclarator(parse_array_dimensions(tokens, symbol_table), loc(c_type))
    else:
        raise ValueError('{l} Expected either (, [ or IDENTIFIER got {got}'.format(
            l=tokens and loc(tokens[0]) or '__EOF__', got=tokens and tokens[0]
        ))

    if tokens and tokens[0] == TOKENS.LEFT_PARENTHESIS:
        location, parameter_types_decl = loc(tokens.pop(0)), []
        if tokens and tokens[0] != TOKENS.RIGHT_PARENTHESIS:
            parameter_types_decl = parameter_type_list(tokens, symbol_table)
        _ = error_if_not_value(tokens, TOKENS.RIGHT_PARENTHESIS)
        set_core_type(c_decl, FunctionType(CType(location), parameter_types_decl, location))
    elif tokens and tokens[0] == TOKENS.LEFT_BRACKET:
        set_core_type(c_decl, parse_array_dimensions(tokens, symbol_table))

    return c_decl


def abstract_declarator(tokens, symbol_table):
    # pointer direct_abstract_declarator? | direct_abstract_declarator
    if tokens and tokens[0] == TOKENS.STAR:
        pointer_type = pointer(tokens)
        if tokens and \
           (tokens[0] in {TOKENS.LEFT_PARENTHESIS, TOKENS.LEFT_BRACKET} or isinstance(tokens[0], IDENTIFIER)):
            c_decl = direct_abstract_declarator(tokens, symbol_table)
            set_core_type(c_decl, pointer_type)
        else:
            c_decl = AbstractDeclarator(pointer_type, loc(pointer_type))
    else:
        c_decl = direct_abstract_declarator(tokens, symbol_table)
    return c_decl


def pointer(tokens):  # parse a list of **1** or or more pointers
    initial_pointer = pointer_type = PointerType(CType(loc(tokens[0])), loc(tokens.pop(0)))
    while tokens and tokens[0] == TOKENS.STAR:
        pointer_type.c_type = PointerType(CType(loc(tokens[0])), loc(tokens.pop(0)))
        pointer_type = c_type(pointer_type)
    return initial_pointer


def storage_class_specifier(tokens, symbol_table):
    """ : TYPEDEF | EXTERN | STATIC | AUTO | REGISTER or tokens """
    return tokens and storage_class_specifier.rules[tokens[0]](tokens, symbol_table)
storage_class_specifier.rules = defaultdict(lambda: lambda *_: None)
storage_class_specifier.rules.update({
    TOKENS.EXTERN: lambda tokens, symbol_table: Extern(loc(tokens.pop(0))),
    TOKENS.STATIC: lambda tokens, symbol_table: Static(loc(tokens.pop(0))),
    TOKENS.REGISTER: lambda tokens, symbol_table: Register(loc(tokens.pop(0))),
    TOKENS.AUTO: lambda tokens, symbol_table: Auto(loc(tokens.pop(0))),
})


def parse_sign_token(tokens, _):
    sign = tokens.pop(0) == TOKENS.UNSIGNED
    token = error_if_not_any_value(tokens, {TOKENS.CHAR, TOKENS.SHORT, TOKENS.INT, TOKENS.LONG})
    return type_specifier.rules[tokens[0]](loc(token), unsigned=sign)


def parse_struct_members(tokens, symbol_table):
    location, members = loc(tokens.pop(0)), OrderedDict()
    while tokens and tokens[0] != TOKENS.RIGHT_BRACE:
        type_spec = type_specifier(tokens, symbol_table)
        while tokens and tokens[0] != TOKENS.SEMICOLON:
            decl = declarator(tokens, symbol_table)
            set_core_type(decl, type_spec)
            if name(decl) in members:
                raise ValueError('{l} Duplicate struct member {name} previous at {at}'.format(
                    l=loc(decl), name=name(decl), at=loc(members[name(decl)])
                ))
            members[name(decl)] = decl
            if tokens and tokens[0] != TOKENS.SEMICOLON:
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
    location = loc(tokens.pop(0))
    if tokens and tokens[0] == TOKENS.LEFT_BRACE:  # anonymous structure.
        return StructType(None, parse_struct_members(tokens, symbol_table), location)

    if tokens and isinstance(tokens[0], IDENTIFIER):
        struct_name = tokens.pop(0)
        if tokens and tokens[0] == TOKENS.LEFT_BRACE:
            obj = StructType(struct_name, parse_struct_members(tokens, symbol_table), loc(struct_name))
            symbol_table[name(obj)] = obj
            return obj
        return symbol_table.get(
            StructType.get_name(struct_name),
            lambda location: StructType(struct_name, None, location)
        )(location)

    raise ValueError('{l} Expected IDENTIFIER or "{" got {got}'.format(
        loc=tokens and loc(tokens[0]) or location, got=tokens and tokens[0]
    ))


def no_type_specifier(tokens, _):
    raise ValueError('{l} Expected a type_specifier or type_name got {got}'.format(
        l=loc(tokens[0]), got=tokens[0]
    ))


def type_specifier(tokens, symbol_table):
    """
        : 'void'
        | ['signed' or 'unsigned'] 'char' | ['signed' or 'unsigned'] 'short'
        | ['signed' or 'unsigned'] 'int' | ['signed' or 'unsigned'] 'long'
        | 'float' | 'double'
        | struct_specifier
        | TYPE_NAME
    """
    if tokens and tokens[0] in type_specifier.rules:
        return type_specifier.rules[tokens[0]](tokens, symbol_table)
    elif tokens and isinstance(symbol_table.get(tokens[0]), CType):
        return symbol_table[tokens[0]](loc(tokens.pop(0)))
    raise ValueError('{l} Expected type_specifier or TYPE_NAME got {got}'.format(l=loc(tokens), got=tokens))
type_specifier.rules = defaultdict(lambda: no_type_specifier)
type_specifier.rules.update({
    TOKENS.STRUCT: struct_specifier,
    TOKENS.SIGNED: parse_sign_token,
    TOKENS.UNSIGNED: parse_sign_token,
})


def type_name(tokens, symbol_table):  #: type_specifier abstract_declarator?   # returns CType
    base_type = type_specifier(tokens, symbol_table)

    if tokens and tokens[0] in {TOKENS.LEFT_PARENTHESIS, TOKENS.LEFT_BRACKET, TOKENS.STAR} \
       or isinstance(tokens[0], IDENTIFIER):
        abs_decl = abstract_declarator(tokens, symbol_table)
        set_core_type(abs_decl, base_type)
        return c_type(abs_decl)

    return base_type