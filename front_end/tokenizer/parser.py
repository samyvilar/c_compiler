__author__ = 'samyvilar'

from collections import defaultdict

from front_end.loader.locations import loc
from front_end.tokenizer.tokens import TOKENS, SYMBOL, KEYWORD, IDENTIFIER, FLOAT, INTEGER, STRING, CHAR, WHITESPACE
from front_end.tokenizer.tokens import PRE_PROCESSING_SYMBOL, letters, digits, alpha_numeric, whitespace
from front_end.errors import error_if_not_value, error_if_empty


def invalid_token(char_stream):
    raise ValueError('{l} Unable to tokenize char {c}'.format(l=loc(char_stream[0]), c=char_stream[0]))


def symbol(char_stream, values, location):
    while char_stream and (values + char_stream[0] in TOKENS.non_keyword_symbols):
        values += char_stream.pop(0)
    return SYMBOL(values, location)


def white_space(_, values, location):
    return WHITESPACE(values, location)


def pre_processor(char_stream, values, location):
    while char_stream and char_stream[0] in {' ', '\t'}:  # remove any leading white_space except for newline
        _ = char_stream.pop(0)
    while char_stream and char_stream[0] in letters:
        values += char_stream.pop(0)

    if values not in TOKENS.pre_processing_directives:
        raise ValueError('{l} Could not locate pre_processing directive {d}'.format(d=values, l=location))
    return PRE_PROCESSING_SYMBOL(values, location)


def number(char_stream, values):
    while char_stream and char_stream[0] in digits:
        values += char_stream.pop(0)
    return values


def number_literal(char_stream, values, location):
    values = number(char_stream, values)
    if char_stream and char_stream[0] == TOKENS.DOT:
        return FLOAT(values + char_stream.pop(0) + number(char_stream, ''), location)
    else:
        return INTEGER(values, location)

escape_characters = {
    'n': '\n',
    't': '\t',
    '0': 0,
    'f': '\f',
    'r': '\r',
    'b': '\b',
}


def string_literal(char_stream, _, location):
    values = ''  # remove leading quote.
    while char_stream and char_stream[0] != TOKENS.DOUBLE_QUOTE:
        if char_stream[0] == '\\':
            _ = char_stream.pop(0)
            values += escape_characters.get(char_stream[0], char_stream.pop(0))
        else:
            values += char_stream.pop(0)
    _ = error_if_not_value(char_stream, TOKENS.DOUBLE_QUOTE)
    return STRING(values, location)


def char_literal(char_stream, _, location):
    error_if_empty(char_stream)
    if char_stream[0] == TOKENS.SINGLE_QUOTE:
        token = CHAR('', location)
    elif char_stream[0] == '\\':
        _ = char_stream.pop(0)
        token = CHAR(escape_characters.get(char_stream[0], char_stream.pop(0)), location)
    else:
        token = CHAR(char_stream.pop(0), location)
    _ = error_if_not_value(char_stream, TOKENS.SINGLE_QUOTE)
    return token


def keyword_or_identifier(char_stream, values, location):
    while char_stream and char_stream[0] in alpha_numeric:
        values += char_stream.pop(0)
    return KEYWORD(values, location) if values in TOKENS.keyword_symbols else IDENTIFIER(values, location)


def dot(char_stream, values, location):
    if char_stream and char_stream[0] in digits:
        values += number(char_stream, '')
        return FLOAT(values, location)
    return SYMBOL(values, location)


def parse(char_stream):
    location, values = loc(char_stream[0]), char_stream.pop(0)
    return parse.rules[values](char_stream, values, location)
parse.rules = {n: number_literal for n in digits}  # rules declared outside so dictionary is only built once.
parse.rules.update({c: keyword_or_identifier for c in letters})
parse.rules.update({s[0]: symbol for s in TOKENS.non_keyword_symbols})
parse.rules.update({w: white_space for w in whitespace})  # assuming all white space are of length 1.
parse.rules.update({
    TOKENS.DOUBLE_QUOTE: string_literal,
    TOKENS.SINGLE_QUOTE: char_literal,
    TOKENS.DOT: dot,
    TOKENS.NUMBER_SIGN: pre_processor,
})  # override symbols ", ', #, .  since they require special rules.


def get_parsing_functions():
    return get_parsing_functions.rules
get_parsing_functions.rules = defaultdict(lambda: invalid_token)  # rules declared outside so dictionary is only built 1
get_parsing_functions.rules.update({
    ch: parse
    for ch in digits | letters | whitespace | {s[0] for s in TOKENS.non_keyword_symbols} | {TOKENS.NUMBER_SIGN}
})
