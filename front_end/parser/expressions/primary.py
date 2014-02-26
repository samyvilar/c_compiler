__author__ = 'samyvilar'

from itertools import imap, izip, repeat, chain
from utils.sequences import peek, consume, peek_or_terminal, takewhile
from utils.rules import set_rules, rules, get_rule, identity
from front_end.loader.locations import loc

from front_end.tokenizer.tokens import TOKENS, IDENTIFIER, CHAR, INTEGER, FLOAT, STRING, HEXADECIMAL, OCTAL
from front_end.tokenizer.tokens import long_long_suffix, long_suffix, unsigned_suffix, suffix

from front_end.parser.declarations.type_name import is_type_name
from front_end.parser.ast.declarations import Declaration, Definition, Declarator
from front_end.parser.ast.expressions import IdentifierExpression, ConstantExpression, CompoundLiteral

from front_end.parser.types import c_type, unsigned, FunctionType
from front_end.parser.types import CharType, StringType, IntegerType, LongType, DoubleType, ArrayType, AddressType

from utils.errors import error_if_not_value, error_if_not_type


def string_literal(tokens):
    location = loc(peek(tokens))    # join adjacent strings into a single string ...
    token = ''.join(takewhile(lambda t: type(t) is STRING, tokens)) + '\0'
    return ConstantExpression(
        imap(char_literal, imap(iter, token)),
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
    return ConstantExpression(_eval(token, rules(integer_literal)[type(token)]), _type, loc(token))
set_rules(integer_literal, ((INTEGER, 10), (HEXADECIMAL, 16), (OCTAL, 8)))


def float_literal(tokens):
    token = consume(tokens)
    return ConstantExpression(float(token), DoubleType(loc(token)), loc(token))


def array_identifier(tokens, symbol_table):
    name = consume(tokens)
    return IdentifierExpression(name, c_type(symbol_table[name])(loc(name)), loc(name))


def function_identifier(tokens, symbol_table):  # function identifiers expr return address to function type ...
    name = consume(tokens)
    return IdentifierExpression(name, AddressType(c_type(symbol_table[name]), loc(name)), loc(name))


def default_identifier(tokens, symbol_table):
    name = consume(tokens)
    return IdentifierExpression(name, c_type(symbol_table[name])(loc(name)), loc(name))


def symbol_identifier(tokens, symbol_table):
    return rules(symbol_identifier)[type(c_type(symbol_table[peek(tokens)]))](tokens, symbol_table)
set_rules(symbol_identifier, ((ArrayType, array_identifier), (FunctionType, function_identifier)), default_identifier)


def constant_identifier(tokens, symbol_table):
    expr = symbol_table[peek(tokens)]
    return ConstantExpression(
        error_if_not_type(exp(expr), (int, long, float)), c_type(expr)(loc(peek(tokens))), loc(consume(tokens))
    )


def identifier_expression(tokens, symbol_table):
    return rules(identifier_expression)[type(symbol_table[peek(tokens)])](tokens, symbol_table)
set_rules(
    identifier_expression,
    chain(
        izip((Declaration, Definition, Declarator), repeat(symbol_identifier)),
        ((ConstantExpression, constant_identifier),)
    )
)


def literal_expression(tokens, symbol_table):
    return rules(literal_expression)[type(peek(tokens))](tokens)
set_rules(
    literal_expression,
    ((CHAR, char_literal), (STRING, string_literal),
     (INTEGER, integer_literal), (OCTAL, integer_literal), (HEXADECIMAL, integer_literal),
     (FLOAT, float_literal))
)


def compound_literal(tokens, symbol_table):
    _ct, _ = symbol_table['__ type_name __'](tokens, symbol_table), error_if_not_value(tokens, TOKENS.RIGHT_PARENTHESIS)
    return CompoundLiteral(symbol_table['__ initializer __'], _ct, loc(_ct))


def expression_or_compound_literal(tokens, symbol_table):
    if error_if_not_value(tokens, TOKENS.LEFT_PARENTHESIS) and is_type_name(peek_or_terminal(tokens), symbol_table):
        return symbol_table['__ compound_literal __'](tokens, symbol_table)
    _exp = symbol_table['__ expression __'](tokens, symbol_table)
    return error_if_not_value(tokens, TOKENS.RIGHT_PARENTHESIS) and _exp


# Primary expression found at the heart of all expressions.
def primary_expression(tokens, symbol_table):   #: IDENTIFIER | CONSTANT | compound_literal | '(' expression ')'
    return get_rule(primary_expression, peek_or_terminal(tokens), hash_funcs=(identity, type))(tokens, symbol_table)
set_rules(
    primary_expression,
    chain(
        izip(rules(literal_expression), repeat(literal_expression)),
        ((IDENTIFIER, identifier_expression), (TOKENS.LEFT_PARENTHESIS, expression_or_compound_literal))
    )
)