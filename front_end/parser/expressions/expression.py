__author__ = 'samyvilar'

from collections import defaultdict
from itertools import product, imap, chain, izip, repeat

from sequences import peek, consume
from front_end.loader.locations import loc, EOFLocation
from front_end.tokenizer.tokens import TOKENS, IDENTIFIER, CONSTANT, CHAR, INTEGER, FLOAT, STRING, HEXADECIMAL, OCTAL
from front_end.tokenizer.tokens import long_long_suffix, long_suffix, unsigned_suffix, suffix

from front_end.parser.types import CharType, StringType, IntegerType, DoubleType, c_type, StructType, ArrayType
from front_end.parser.types import IntegralType, NumericType, LongType, safe_type_coercion, unsigned, UnionType
from front_end.parser.ast.expressions import ConstantExpression, IdentifierExpression, EmptyExpression
from front_end.parser.ast.expressions import CastExpression, CompoundLiteral, CommaExpression, exp

from front_end.parser.symbol_table import SymbolTable

import front_end.parser.expressions.postfix as postfix
import front_end.parser.expressions.unary as unary

from front_end.parser.expressions.binary import assignment_expression, logical_or_expression
from front_end.parser.declarations.declarators import type_name, is_type_name


from front_end.parser.expressions.reduce import reduce_expression

from front_end.errors import error_if_not_value, error_if_empty, error_if_not_type

from logging_config import logging


logger = logging.getLogger('parser')


def designations(tokens, symbol_table, _ctype, default_designations):
    # ('[' positive_integral (... positive_integral)? ']' or '.'IDENTIFIER)+
    if peek(tokens, '') == TOKENS.LEFT_BRACKET:
        _, _ = error_if_not_type(_ctype, ArrayType), consume(tokens)
        first = last = constant_expression(tokens, symbol_table)
        if peek(tokens, '') == TOKENS.ELLIPSIS:
            _, last = consume(tokens), constant_expression(tokens, symbol_table)
        _ = error_if_not_value(tokens, TOKENS.RIGHT_BRACKET)
        _, _ = error_if_not_type(c_type(first), IntegralType), error_if_not_type(c_type(last), IntegralType)
        if exp(first) < 0 or exp(last) < 0:
            value = (exp(first) < 0 and first) or (exp(last) < 0 and last)
            raise ValueError('{l} array indices must be greater than or equal to 0 got {g}'.format(
                l=loc(value), g=exp(value)
            ))
        if exp(last) - exp(first) < 0:
            raise ValueError('{l} array indices generate empty range'.format(l=loc(first)))
        if exp(last) >= len(_ctype):
            raise ValueError('{l} array indices exceed array bounds'.format(l=loc(last)))
        if exp(first) >= len(_ctype):
            raise ValueError('{l} array indices exceed array bounds'.format(l=loc(first)))
        values = ((index,) for index in xrange(exp(first), exp(last) + 1))
    elif peek(tokens, '') == TOKENS.DOT:
        _, _ = consume(tokens), error_if_not_type(_ctype, StructType)
        ident = error_if_not_type(consume(tokens, EOFLocation), IDENTIFIER)
        if ident not in _ctype:
            raise ValueError('{l} identifier designator {ident} not in {c}'.format(l=loc(ident), ident=ident, c=_ctype))
        values = ((_ctype.offset(ident),),)
        _ctype = _ctype.members[ident]
    else:
        return default_designations, _ctype

    if peek(tokens, '') in {TOKENS.LEFT_BRACKET, TOKENS.DOT}:
        next_designations, _ctype = designations(tokens, symbol_table, c_type(_ctype), ())
        values = imap(chain.from_iterable, product(values, next_designations))
    else:
        _ = error_if_not_value(tokens, TOKENS.EQUAL)
    return values, _ctype


def _value(tokens, symbol_table, ctype, default_designation):
    # ((designation '=')? (assignment_expression or initializer))
    desig, ctype = peek(tokens, '') in {TOKENS.LEFT_BRACKET, TOKENS.DOT} and designations(
        tokens, symbol_table, ctype, default_designation
    ) or (default_designation, ctype)

    value = (
        peek(tokens, '') == TOKENS.LEFT_BRACE and initializer(tokens, symbol_table, c_type(ctype))
    ) or assignment_expression(tokens, symbol_table, cast_expression)

    return value, desig


def initializer_list(tokens, symbol_table, ctype, values):
    # designation_value_pair (',' designation_value_pair)*
    expr, designations = _value(tokens, symbol_table, ctype, default_designation=(
        (isinstance(ctype, (StructType, ArrayType)) and ((0,),)) or ((),)
    ))

    prev_designation = set_expr_designations(designations, expr, values, ctype)
    while peek(tokens, '') == TOKENS.COMMA:
        _ = consume(tokens)
        expr, designations = _value(tokens, symbol_table, ctype, ((prev_designation + 1,),))
        prev_designation = set_expr_designations(designations, expr, values, ctype)
    return values


def initializer(tokens, symbol_table, ctype):
    # '{' initializer* '}'
    _ = error_if_not_value(tokens, TOKENS.LEFT_BRACE)
    values = (
        peek(tokens, '') != TOKENS.RIGHT_BRACE and initializer_list(tokens, symbol_table, ctype, defaults(ctype))
    ) or defaults(ctype)
    _ = error_if_not_value(tokens, TOKENS.RIGHT_BRACE)
    return values


def max_length(ctypes):
    def _len(ctype):
        if isinstance(ctype, ArrayType):
            return len(ctype) * _len(c_type(ctype))
        elif isinstance(ctype, UnionType):
            return max_length(ctype)
        elif isinstance(ctype, StructType):
            return sum(imap(_len, imap(c_type, ctype.members.itervalues())))
        elif isinstance(ctype, NumericType):
            return 1
        else:
            raise TypeError("{l} Expected a ctype got {g}".format(l=loc(ctype), g=ctype))

    max_type = next(ctypes, ArrayType(CharType(), 0))
    for ctype in ctypes:
        if _len(max_type) < _len(ctype):
            max_type = ctype
    return max_type


def defaults(ctype):
    if isinstance(ctype, ArrayType):
        return CompoundLiteral((defaults(c_type(ctype)) for _ in xrange(len(ctype))), ctype)
    elif isinstance(ctype, UnionType):  # Unions are a subtype of Struct hence we need to check them first ...
        # assuming all numeric types are of the same length, TODO: deal with variable sizes ...
        return CompoundLiteral(defaults(max_length(imap(c_type, ctype.members.itervalues()))), ctype)
    elif isinstance(ctype, StructType):
        return CompoundLiteral((defaults(c_type(ctype.members[member_name])) for member_name in ctype.members), ctype)
    elif isinstance(ctype, NumericType):
        return CompoundLiteral((EmptyExpression(ctype, loc(ctype)),), ctype)
    else:
        raise ValueError('{l} Unable to generate default expression for ctype {c}'.format(l=loc(ctype), c=ctype))


def set_expr_designations(designations, expr, values, _ctype):
    initial_designation = 0
    for des in designations:
        initial_designation = set_designated_expression(des, expr, values, _ctype)
    return initial_designation


def set_designated_expression(designation, expr, values, _ctype):
    initial_designation = None
    for des in designation:
        if initial_designation is None:
            initial_designation = des

        if des >= len(values):
            values = False
            break

        # All unions have a zero offset ...
        # TODO: better implement this, as of now we are using the offset to the expected c_type of the expression
        # hence we can't update Union.offset to properly return 0 since it would get the wrong type when initializing
        # something besides the first element ...
        values = values[0 if isinstance(_ctype, UnionType) else des]
        _ctype = c_type((isinstance(_ctype, StructType) and _ctype.members.values()[des]) or _ctype)

    if not values:
        logger.warning('{l} excess elements in initializer, expression will be ignored!'.format(l=loc(expr)))
    else:
        if isinstance(c_type(expr), (ArrayType, StructType)):
            for index, sub_expr in enumerate(exp(expr)):
                _ = set_designated_expression(
                    (index,),
                    (isinstance(c_type(sub_expr), (ArrayType, StructType)) and sub_expr) or sub_expr[0],
                    values,
                    _ctype
                )
        else:
            if not safe_type_coercion(_ctype, c_type(expr)):
                raise ValueError('{l} Unable to coerce from {f} to {t}'.format(l=loc(expr), f=_ctype, t=c_type(expr)))
            assert len(values) == 1
            values[0] = cast(expr, _ctype)
    return initial_designation or 0


def string_literal(tokens):
    token = ''
    location = loc(peek(tokens))
    while type(peek(tokens, None)) is STRING:
        token += consume(tokens)
    token += '\0'
    return ConstantExpression(
        (ConstantExpression(ord(c), CharType(location), location) for c in token),
        StringType(len(token), location),
        location
    )


def char_literal(tokens):
    token = consume(tokens)
    return ConstantExpression(ord(token), CharType(loc(token)), loc(token))


def get_type(suffix_str, location):
    _type, _eval = IntegerType(location, unsigned=unsigned_suffix in suffix_str), int
    _type, _eval = (long_suffix in suffix_str and LongType(_type, loc(_type), unsigned(_type))) or _type, long
    _type, _eval = (long_long_suffix in suffix_str and LongType(_type, loc(_type), unsigned(_type))) or _type, long
    return _type, _eval


def integer_literal(tokens):
    token = consume(tokens)
    _type, _eval = get_type(suffix(token).lower(), loc(token))
    return ConstantExpression(
        _eval(token, (isinstance(token, HEXADECIMAL) and 16) or (isinstance(token, OCTAL) and 8) or 10),
        _type,
        loc(token)
    )


def float_literal(tokens):
    token = consume(tokens)
    return ConstantExpression(float(token), DoubleType(loc(token)), loc(token))


def literal(tokens, symbol_table):  # assignment_expression
    return assignment_expression(tokens, symbol_table, cast_expression)


def literals(tokens, symbol_table):
    # '{' (literal ',')* '}'
    _ = error_if_not_value(tokens, TOKENS.LEFT_BRACE)
    while peek(tokens, '') != TOKENS.RIGHT_BRACE:
        yield literal(tokens, symbol_table)
        _ = peek(tokens, '') == TOKENS.COMMA and consume(tokens)
    _ = error_if_not_value(tokens, TOKENS.RIGHT_BRACE)


def compound_literal(tokens, symbol_table, ctype):
    return initializer(tokens, symbol_table, ctype)


# Primary expression found at the heart of all expressions.
def primary_expression(tokens, symbol_table):   #: IDENTIFIER | constant | '(' expression ')'
    if isinstance(peek(tokens, ''), IDENTIFIER):
        identifier = consume(tokens)
        return IdentifierExpression(identifier, c_type(symbol_table[identifier]), loc(identifier))

    if isinstance(peek(tokens, ''), CONSTANT):
        rules = {
            CHAR: char_literal,
            STRING: string_literal,
            INTEGER: integer_literal,
            OCTAL: integer_literal,
            HEXADECIMAL: integer_literal,
            FLOAT: float_literal,
        }
        return rules[type(peek(tokens))](tokens)

    if peek(tokens, '') == TOKENS.LEFT_PARENTHESIS:
        _ = consume(tokens)
        exp = expression(tokens, symbol_table)
        _ = error_if_not_value(tokens, TOKENS.RIGHT_PARENTHESIS)
        return exp

    raise ValueError('{l} Could not parse primary_expression, expected IDENTIFIER, CONSTANT, ( got {token}'.format(
        l=loc(peek(tokens, EOFLocation)), token=peek(tokens, '')
    ))


def postfix_expression(tokens, symbol_table, primary_exp=None):
    """
    :   ( '(' TYPE_NAME ')' '{' INITIALIZER_LIST '}' or primary_expression)
            (   '[' expression ']'
            |   '(' ')'
            |   '(' argument_expression_list ')'
            |   '.' IDENTIFIER
            |   '->' IDENTIFIER
            |   '++'
            |   '--'
            )*
    """
    if primary_exp is None:
        if peek(tokens, '') == TOKENS.LEFT_PARENTHESIS:
            # Again slight ambiguity since primary_expression may start with '(' expression ')'
            # can't call cast_expression since it will try to call postfix_expression.
            _ = consume(tokens)
            if is_type_name(peek(tokens, ''), symbol_table):
                ctype, _ = type_name(tokens, symbol_table), error_if_not_value(tokens, TOKENS.RIGHT_PARENTHESIS)
                primary_exp = compound_literal(tokens, symbol_table, ctype)
            else:
                primary_exp = expression(tokens, symbol_table)
                _ = error_if_not_value(tokens, TOKENS.RIGHT_PARENTHESIS)
        else:
            primary_exp = primary_expression(tokens, symbol_table)

    # noinspection PyUnresolvedReferences
    while peek(tokens, '') in postfix_expression.rules:
        primary_exp = postfix_expression.rules[peek(tokens)](tokens, symbol_table, primary_exp, expression)

    return primary_exp
postfix_expression.rules = {
    TOKENS.LEFT_BRACKET: postfix.subscript_oper,
    TOKENS.LEFT_PARENTHESIS: postfix.function_call,
    TOKENS.DOT: postfix.dot_oper,
    TOKENS.ARROW: postfix.arrow_operator,
    TOKENS.PLUS_PLUS: postfix.inc_dec,
    TOKENS.MINUS_MINUS: postfix.inc_dec,
}


@reduce_expression
def unary_expression(tokens, symbol_table):
    """
        : postfix_expression
        | '++' unary_expression
        | '--' unary_expression
        | unary_operator cast_expression
        | 'sizeof' '(' type_name |  unary_expression ')'
    """
    error_if_empty(tokens)
    if peek(tokens, '') in unary_expression.rules and not isinstance(peek(tokens), CONSTANT):
        # unary_operators are followed by a cast_expression
        exp_func = (peek(tokens, '') in unary.unary_operator.rules and cast_expression) or unary_expression
        return unary_expression.rules[peek(tokens)](tokens, symbol_table, exp_func)

    return postfix_expression(tokens, symbol_table)
unary_expression.rules = defaultdict(lambda: unary.no_rule_found)
unary_expression.rules.update(chain(
    izip(unary.unary_operator.rules, repeat(unary.unary_operator)),
    (
        (TOKENS.PLUS_PLUS, unary.increment_decrement),
        (TOKENS.MINUS_MINUS, unary.increment_decrement),
        (TOKENS.SIZEOF, unary.size_of),
    )
))


@reduce_expression
def cast(expr, to_type):
    return CastExpression(expr, to_type, loc(to_type))


@reduce_expression
def cast_expression(tokens, symbol_table):
    # : '(' type_name ')' cast_expression | unary_expression
    # There is a slight ambiguity here, both cast_expression and primary expression may begin with '('
    # but only cast expression maybe followed by type_name.
    if peek(tokens, '') == TOKENS.LEFT_PARENTHESIS:
        _, current_token = consume(tokens), peek(tokens, '')
        if is_type_name(current_token, symbol_table):
            obj, _ = type_name(tokens, symbol_table), error_if_not_value(tokens, TOKENS.RIGHT_PARENTHESIS)
            # There is a second ambiguity between cast_expression and postfix_expression, since postfix_expression
            # may have compound_literal which is a cast_expression followed by an initializer_list enclosed in braces.
            if peek(tokens, '') == TOKENS.LEFT_BRACE:
                return postfix_expression(
                    tokens,
                    symbol_table,
                    primary_exp=compound_literal(tokens, symbol_table, obj)
                )
            else:
                return cast(cast_expression(tokens, symbol_table), obj)
        else:
            # Found '(' but could not generate type_name! so we have to try unary_expression but the token stream
            # has already consume '(' so we have to generate the primary_expression manually, since peek/consume
            # reference the same token sequence and using chain would create a new token sequence ...
            # while we could use tee it would still consume from the original iterator, corrupting peek/consume!

            # unary_expression -> postfix_expression -> primary_expression (postfix_expression)*

            # This is the only way to deal with the ambiguity without modifying the token stream and
            # creating havoc ...

            prim_exp, _ = expression(tokens, symbol_table), error_if_not_value(tokens, TOKENS.RIGHT_PARENTHESIS)
            return postfix_expression(tokens, symbol_table, primary_exp=prim_exp)
    else:
        return unary_expression(tokens, symbol_table)


def expression(tokens, symbol_table=None):
    # assignment_expression (',' assignment_expression)*
    symbol_table = symbol_table or SymbolTable()

    expr = assignment_expression(tokens, symbol_table, cast_expression)

    if peek(tokens, '') == TOKENS.COMMA:
        expr = [expr]
        while peek(tokens, '') == TOKENS.COMMA:
            _ = consume(tokens)
            expr.append(assignment_expression(tokens, symbol_table, cast_expression))
        expr = CommaExpression(expr, c_type(expr[-1]), loc(expr[-1]))

    return expr


def constant_expression(tokens, symbol_table):
    const_exp = logical_or_expression(tokens, symbol_table, cast_expression)

    if isinstance(const_exp, IdentifierExpression) and \
            isinstance(symbol_table.get(exp(const_exp), type), ConstantExpression):
        const_exp = symbol_table[exp(const_exp)]

    if not isinstance(const_exp, ConstantExpression):
        raise ValueError('{l} Expected a constant expression got {got}'.format(l=loc(const_exp), got=const_exp))
    return const_exp