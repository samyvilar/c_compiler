from sequences import values

__author__ = 'samyvilar'

import string
from front_end.loader.locations import LocationNotSet
from front_end.loader.load import Str

letters = set(string.letters) | {'_'}
digits = set(string.digits)
alpha_numeric = digits | letters
whitespace = set(string.whitespace) | {' ', '\a'}


class Symbol(Str):
    pass


class PreprocessorSymbol(Symbol):
    pass


class KeywordSymbol(Symbol):
    pass


class WhiteSpace(Symbol):
    pass


class TOKENS(object):
    EQUAL = Symbol('=')
    PLUS = Symbol('+')
    MINUS = Symbol('-')
    STAR = Symbol('*')
    FORWARD_SLASH = Symbol('/')
    PERCENTAGE = Symbol('%')
    AMPERSAND = Symbol('&')
    COMMA = Symbol(',')
    SEMICOLON = Symbol(';')
    COLON = Symbol(':')
    DOT = Symbol('.')
    EXCLAMATION = Symbol('!')
    LEFT_PARENTHESIS = Symbol('(')
    RIGHT_PARENTHESIS = Symbol(')')
    LEFT_BRACKET = Symbol('[')
    RIGHT_BRACKET = Symbol(']')
    LEFT_BRACE = Symbol('{')
    RIGHT_BRACE = Symbol('}')
    TILDE = Symbol('~')
    LESS_THAN = Symbol('<')
    GREATER_THAN = Symbol('>')
    BAR = Symbol('|')
    CARET = Symbol('^')
    DOUBLE_QUOTE = Symbol('"')
    SINGLE_QUOTE = Symbol("'")

    LOGICAL_AND = Symbol('&&')
    PLUS_PLUS = Symbol('++')
    MINUS_MINUS = Symbol('--')

    NOT_EQUAL = Symbol('!=')
    PERCENTAGE_EQUAL = Symbol('%=')
    AMPERSAND_EQUAL = Symbol('&=')
    STAR_EQUAL = Symbol('*=')
    PLUS_EQUAL = Symbol('+=')
    MINUS_EQUAL = Symbol('-=')
    ARROW = Symbol('->')
    FORWARD_SLASH_EQUAL = Symbol('/=')
    SHIFT_LEFT = Symbol('<<')
    LESS_THAN_OR_EQUAL = Symbol('<=')
    EQUAL_EQUAL = Symbol('==')
    GREATER_THAN_OR_EQUAL = Symbol('>=')
    SHIFT_RIGHT = Symbol('>>')
    CARET_EQUAL = Symbol('^=')
    BAR_EQUAL = Symbol('|=')
    LOGICAL_OR = Symbol('||')

    SHIFT_LEFT_EQUAL = Symbol('<<=')
    SHIFT_RIGHT_EQUAL = Symbol('>>=')

    # IDs of all keywords
    SIZEOF = KeywordSymbol('sizeof')
    BREAK = KeywordSymbol('break')
    CASE = KeywordSymbol('case')
    CHAR = KeywordSymbol('char')
    CONTINUE = KeywordSymbol('continue')
    DEFAULT = KeywordSymbol('default')
    DO = KeywordSymbol('do')
    DOUBLE = KeywordSymbol('double')
    ELSE = KeywordSymbol('else')
    FLOAT = KeywordSymbol('float')
    FOR = KeywordSymbol('for')
    GOTO = KeywordSymbol('goto')
    IF = KeywordSymbol('if')
    INT = KeywordSymbol('int')
    LONG = KeywordSymbol('long')
    RETURN = KeywordSymbol('return')
    SHORT = KeywordSymbol('short')
    SIGNED = KeywordSymbol('signed')
    STRUCT = KeywordSymbol('struct')
    SWITCH = KeywordSymbol('switch')
    UNSIGNED = KeywordSymbol('unsigned')
    VOID = KeywordSymbol('void')
    WHILE = KeywordSymbol('while')
    TYPEDEF = KeywordSymbol('typedef')
    EXTERN = KeywordSymbol('extern')
    STATIC = KeywordSymbol('static')
    AUTO = KeywordSymbol('auto')
    REGISTER = KeywordSymbol('register')

    NUMBER_SIGN = Symbol('#')
    PINCLUDE = PreprocessorSymbol('#include')
    PDEFINE = PreprocessorSymbol('#define')
    PUNDEF = PreprocessorSymbol('#undef')

    PIF = PreprocessorSymbol('#if')
    PELIF = PreprocessorSymbol('#elif')
    PELSE = PreprocessorSymbol('#else')
    PIFDEF = PreprocessorSymbol('#ifdef')
    PIFNDEF = PreprocessorSymbol('#ifndef')
    PENDIF = PreprocessorSymbol('#endif')
    DEFINED = PreprocessorSymbol('defined')

    non_keyword_symbols = set()
    keyword_symbols = set()
    pre_processing_directives = set()


TOKENS.keyword_symbols = {
    getattr(TOKENS, symbol)
    for symbol in dir(TOKENS)
    if isinstance(getattr(TOKENS, symbol), KeywordSymbol)
}

TOKENS.non_keyword_symbols = {
    getattr(TOKENS, symbol)
    for symbol in dir(TOKENS)
    if type(getattr(TOKENS, symbol)) is Symbol
    and getattr(TOKENS, symbol) not in TOKENS.keyword_symbols
}

TOKENS.pre_processing_directives = {
    getattr(TOKENS, symbol)
    for symbol in dir(TOKENS)
    if isinstance(getattr(TOKENS, symbol), PreprocessorSymbol)
}


class TOKEN(Str):
    pass


class CONSTANT(TOKEN):
    pass


class STRING(CONSTANT):
    pass


class CHAR(CONSTANT):
    pass


class INTEGER(CONSTANT):
    pass


class FLOAT(CONSTANT):
    pass


class IDENTIFIER(TOKEN):
    pass


class KEYWORD(TOKEN):
    pass


class SYMBOL(TOKEN):
    pass


class IGNORE(TOKEN):
    pass


class WHITESPACE(IGNORE):
    pass


class COMMENT(IGNORE):
    pass


class SINGLE_LINE_COMMENT(COMMENT):
    pass


class MULTI_LINE_COMMENT(COMMENT):
    pass


class PRE_PROCESSING_SYMBOL(TOKEN):
    # noinspection PyInitNewSignature
    def __new__(cls, values, location=LocationNotSet):
        if values not in TOKENS.pre_processing_directives:
            raise ValueError('{l} Could not locate pre_processing directive {d}'.format(l=locatio, d=values))
        return super(PRE_PROCESSING_SYMBOL, cls).__new__(cls, values, location)