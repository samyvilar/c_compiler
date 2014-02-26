__author__ = 'samyvilar'

import string
from itertools import imap, chain, repeat, ifilter, ifilterfalse
from utils.sequences import permute_case, consume
from front_end.loader.locations import LocationNotSet, loc
from front_end.loader.load import Str

from utils.errors import raise_error


letters = set(string.letters) | {'_'}
digits = set(string.digits)

octal_digits = digits - {'9', '8'}
hexadecimal_digits = digits | {'a', 'b', 'c', 'd', 'e', 'f', 'A', 'B', 'C', 'D', 'E', 'F'}
hexadecimal_prefix = '0x', '0X'
octal_prefix = '0',
alpha_numeric = digits | letters
whitespace = set(string.whitespace) | {' ', '\a'}

unsigned_suffix = 'u'
long_suffix = 'l'
long_long_suffix = long_suffix + long_suffix

lower_case_suffix = {unsigned_suffix, long_suffix, long_long_suffix}
lower_case_possible_numeric_suffix = lower_case_suffix | {
    unsigned_suffix + long_suffix,
    long_suffix + unsigned_suffix,
    unsigned_suffix + long_long_suffix,
    long_long_suffix + unsigned_suffix
}
numeric_suffix_letters = {unsigned_suffix, unsigned_suffix.upper(), long_suffix, long_suffix.upper()}
possible_numeric_suffix = set(chain.from_iterable(imap(permute_case, lower_case_possible_numeric_suffix))) | {''}


def digit(number):
    return string.digits[number]


class Symbol(Str):
    pass


class PreprocessorSymbol(Symbol):
    pass


class KeywordSymbol(Symbol):
    pass


class WhiteSpace(Symbol):
    pass


class TOKENS(object):
    QUESTION = Symbol('?')

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
    ELLIPSIS = Symbol('...')

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

    START_OF_COMMENT = Symbol('//')
    START_OF_MULTI_LINE_COMMENT = Symbol('/*')
    END_OF_MULTI_LINE_COMMENT = Symbol('*/')

    # IDs of all keywords
    AUTO = KeywordSymbol('auto')

    BREAK = KeywordSymbol('break')
    CASE = KeywordSymbol('case')
    CHAR = KeywordSymbol('char')
    CONST = KeywordSymbol('const')
    CONTINUE = KeywordSymbol('continue')
    DEFAULT = KeywordSymbol('default')
    DO = KeywordSymbol('do')
    DOUBLE = KeywordSymbol('double')
    ELSE = KeywordSymbol('else')
    ENUM = KeywordSymbol('enum')
    EXTERN = KeywordSymbol('extern')
    FLOAT = KeywordSymbol('float')
    FOR = KeywordSymbol('for')
    GOTO = KeywordSymbol('goto')
    IF = KeywordSymbol('if')
    INT = KeywordSymbol('int')
    LONG = KeywordSymbol('long')
    REGISTER = KeywordSymbol('register')
    RETURN = KeywordSymbol('return')
    SHORT = KeywordSymbol('short')
    SIGNED = KeywordSymbol('signed')
    SIZEOF = KeywordSymbol('sizeof')
    STATIC = KeywordSymbol('static')
    STRUCT = KeywordSymbol('struct')
    SWITCH = KeywordSymbol('switch')
    TYPEDEF = KeywordSymbol('typedef')
    UNION = KeywordSymbol('union')
    UNSIGNED = KeywordSymbol('unsigned')
    VOID = KeywordSymbol('void')
    VOLATILE = KeywordSymbol('volatile')
    WHILE = KeywordSymbol('while')

    PINCLUDE = PreprocessorSymbol('#include')
    PDEFINE = PreprocessorSymbol('#define')
    PUNDEF = PreprocessorSymbol('#undef')

    NUMBER_SIGN = PreprocessorSymbol('#')
    PP = PreprocessorSymbol('##')

    PIF = PreprocessorSymbol('#if')
    PELIF = PreprocessorSymbol('#elif')
    PELSE = PreprocessorSymbol('#else')
    PIFDEF = PreprocessorSymbol('#ifdef')
    PIFNDEF = PreprocessorSymbol('#ifndef')
    PENDIF = PreprocessorSymbol('#endif')
    DEFINED = PreprocessorSymbol('defined')
    PWARNING = PreprocessorSymbol('#warning')
    PERROR = PreprocessorSymbol('#error')

    non_keyword_symbols = set()
    keyword_symbols = set()
    pre_processing_directives = set()


all_symbols = set(ifilter(lambda symbol: isinstance(symbol, Symbol), imap(getattr, repeat(TOKENS), dir(TOKENS))))

TOKENS.keyword_symbols = set(ifilter(lambda symbol: isinstance(symbol, KeywordSymbol), all_symbols))

TOKENS.non_keyword_symbols = set(
    ifilter(lambda symbol: type(symbol) is Symbol and symbol not in TOKENS.keyword_symbols, all_symbols)
)

TOKENS.pre_processing_directives = set(ifilter(lambda symbol: isinstance(symbol, PreprocessorSymbol), all_symbols))


class TOKEN(Str):
    def __repr__(self):
        return self


class CONSTANT(TOKEN):
    pass


class STRING(CONSTANT):
    def __repr__(self):
        return '"' + str.__repr__(self)[1:-1] + '"'


class CHAR(CONSTANT):
    def __repr__(self):
        return "'" + str.__repr__(self)[1:-1] + "'"


class INTEGER(CONSTANT):
    def __new__(cls, value, location=LocationNotSet, suffix=''):
        value = super(INTEGER, cls).__new__(cls, value, location)
        value.suffix = suffix
        return value


class HEXADECIMAL(INTEGER):
    pass


class OCTAL(INTEGER):
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
    def __new__(cls, value='', location=LocationNotSet):
        return super(IGNORE, cls).__new__(cls, value, location)


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
        _ = values not in TOKENS.pre_processing_directives and raise_error(
            '{l} Could not locate pre_processing directive {d}'.format(l=location, d=values)
        )
        return super(PRE_PROCESSING_SYMBOL, cls).__new__(cls, values, location)


def suffix(token):
    return getattr(token, 'suffix')


def copy_token(token, new_location=LocationNotSet):
    if hasattr(token, 'suffix'):
        return token.__new__(token.__class__, str(token), new_location or loc(token), suffix=suffix(token))
    return token.__new__(token.__class__, str(token), new_location or loc(token))


def filter_out_empty_tokens(tokens, obj_type=IGNORE):
    return ifilterfalse(lambda t, obj_type=obj_type: isinstance(t, obj_type), imap(consume, repeat(iter(tokens))))


empty_token = IGNORE()