__author__ = 'samyvilar'

from sequences import peek, consume, takewhile

from front_end.loader.locations import loc
from front_end.tokenizer.tokens import TOKENS, SYMBOL, KEYWORD, IDENTIFIER, FLOAT, INTEGER, STRING, CHAR, WHITESPACE
from front_end.tokenizer.tokens import PRE_PROCESSING_SYMBOL, letters, digits, alpha_numeric, whitespace
from front_end.tokenizer.tokens import SINGLE_LINE_COMMENT, MULTI_LINE_COMMENT
from front_end.errors import error_if_not_value


def get_line(values):  # get all the tokens on the current line, being that preprocessor work on a line-by-line basis
    line_number = loc(peek(values)).line_number
    return takewhile(lambda token: loc(token).line_number == line_number, values)


def single_line_comment(char_stream, location):
    return SINGLE_LINE_COMMENT(''.join(get_line(char_stream)), location)


def multi_line_comment(char_stream, location):
    values = ''
    seen_star = False
    while peek(char_stream, default=False):
        values += consume(char_stream)
        if values[-1] == TOKENS.FORWARD_SLASH and seen_star:
            break
        elif values[-1] == TOKENS.STAR:
            seen_star = True
        else:
            seen_star = False
    if seen_star:
        return MULTI_LINE_COMMENT(values, location)
    raise ValueError('{l} Could no locate end of multi-line comment.'.format(l=location))


def comment(char_stream, location):
    forward_slash = consume(char_stream)
    if peek(char_stream, default='') == TOKENS.FORWARD_SLASH:
        token = single_line_comment(char_stream, location)
    elif peek(char_stream, default='') == TOKENS.STAR:
        token = multi_line_comment(char_stream, location)
    else:
        token = SYMBOL(forward_slash, loc(forward_slash))
    return token


def symbol(char_stream, location):
    values = consume(char_stream)
    while peek(char_stream, default=False) and (values + peek(char_stream) in TOKENS.non_keyword_symbols):
        values += consume(char_stream)
    return SYMBOL(values, location)


def white_space(char_stream, location):
    return WHITESPACE(consume(char_stream), location)


def pre_processor(char_stream, location):
    values = consume(char_stream) + ''.join(takewhile(lambda char: char in letters, char_stream))
    return PRE_PROCESSING_SYMBOL(values, location)


def number(char_stream):
    return ''.join(takewhile(lambda char: char in digits, char_stream))


def number_literal(char_stream, location):
    values = number(char_stream)
    if peek(char_stream, default='') == TOKENS.DOT:
        return FLOAT(values + consume(char_stream) + number(char_stream), location)
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


def string_literal(char_stream, location):
    _ = consume(char_stream)
    values = ''
    while peek(char_stream, default='') != TOKENS.DOUBLE_QUOTE:
        if peek(char_stream) == '\\':
            _ = consume(char_stream)
            values += escape_characters.get(peek(char_stream), consume(char_stream))
        else:
            values += consume(char_stream)
    _ = error_if_not_value(char_stream, TOKENS.DOUBLE_QUOTE)
    return STRING(values, location)


def char_literal(char_stream, location):
    _ = consume(char_stream)
    char = consume(char_stream)
    if char == TOKENS.SINGLE_QUOTE:
        return CHAR('', location)

    if char == '\\':
        token = CHAR(escape_characters.get(peek(char_stream), consume(char_stream)), location)
    else:
        token = CHAR(char, location)
    _ = error_if_not_value(char_stream, TOKENS.SINGLE_QUOTE)
    return token


def keyword_or_identifier(char_stream, location):
    values = ''.join(takewhile(lambda char: char in alpha_numeric, char_stream))
    return KEYWORD(values, location) if values in TOKENS.keyword_symbols else IDENTIFIER(values, location)


def dot(char_stream, location):
    values = consume(char_stream)
    if peek(char_stream, default='') in digits:
        return FLOAT(values + number(char_stream), location)
    return SYMBOL(values, location)


def parse(char_stream):
    return parse.rules[peek(char_stream)](char_stream, loc(peek(char_stream)))
parse.rules = {n: number_literal for n in digits}  # rules declared outside so dictionary is only built once.
parse.rules.update({c: keyword_or_identifier for c in letters})
parse.rules.update({s[0]: symbol for s in TOKENS.non_keyword_symbols})
parse.rules.update({w: white_space for w in whitespace})  # assuming all white space are of length 1.
parse.rules.update({
    TOKENS.DOUBLE_QUOTE: string_literal,
    TOKENS.SINGLE_QUOTE: char_literal,
    TOKENS.DOT: dot,
    TOKENS.NUMBER_SIGN: pre_processor,
    TOKENS.FORWARD_SLASH: comment,  # override forward slash to deal with comments // /*
})  # override symbols ", ', #, .  since they require special rules.


def get_directives():
    return get_directives.rules
get_directives.rules = {
    ch: parse
    for ch in digits | letters | whitespace | {s[0] for s in TOKENS.non_keyword_symbols} | {TOKENS.NUMBER_SIGN}
}