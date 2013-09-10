__author__ = 'samyvilar'

from itertools import chain, izip, repeat, imap

from sequences import peek, consume, takewhile

from front_end.loader.locations import loc, EOFLocation
from front_end.tokenizer.tokens import TOKENS, SYMBOL, KEYWORD, IDENTIFIER, FLOAT, INTEGER, STRING, CHAR, WHITESPACE
from front_end.tokenizer.tokens import HEXADECIMAL, OCTAL
from front_end.tokenizer.tokens import PRE_PROCESSING_SYMBOL, letters, alpha_numeric, whitespace
from front_end.tokenizer.tokens import digits, hexadecimal_digits, hexadecimal_prefix, octal_prefix
from front_end.tokenizer.tokens import possible_numeric_suffix
from front_end.tokenizer.tokens import SINGLE_LINE_COMMENT, MULTI_LINE_COMMENT
from front_end.errors import error_if_not_value


def get_line(values):  # get all the tokens on the current line, being that preprocessor work on a line-by-line basis
    return takewhile(lambda token, line_number=loc(peek(values, EOFLocation)).line_number:
                     loc(token).line_number == line_number, values)


def single_line_comment(char_stream, location):
    return SINGLE_LINE_COMMENT(''.join(get_line(char_stream)), location)


def multi_line_comment(char_stream, location):
    values = ''
    seen_star = False
    while peek(char_stream, ''):
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
    if is_adjacent(char_stream, TOKENS.FORWARD_SLASH, loc(forward_slash).column_number + 1):
        token = single_line_comment(char_stream, location)
    elif is_adjacent(char_stream, TOKENS.STAR, loc(forward_slash).column_number + 1):
        token = multi_line_comment(char_stream, location)
    else:
        token = symbol(char_stream, location, values=forward_slash)
    return token


def is_adjacent(stream, value, column_number, terminal=object()):
    return peek(stream, terminal) == value and column_number == loc(peek(stream, EOFLocation)).column_number


def symbol(char_stream, location, values=None):
    values = values or consume(char_stream)
    while peek(char_stream, '') and (values + peek(char_stream) in TOKENS.non_keyword_symbols):
        values += consume(char_stream)

    next_char = peek(char_stream, '')
    if values == TOKENS.DOT:
        if next_char in digits and is_adjacent(char_stream, next_char, location.column_number + len(values)):
            return FLOAT(values + number(char_stream), location)
        if is_adjacent(char_stream, TOKENS.DOT, location.column_number + len(values)):
            values += consume(char_stream)
            if is_adjacent(char_stream, TOKENS.DOT, location.column_number + len(values)):
                values += consume(char_stream)
                return SYMBOL(values, location)  # TOKENS.ELLIPSIS
            raise ValueError('{l} Unable to tokenize: `{t}`'.format(l=location, t=TOKENS.DOT + TOKENS.DOT))
    return SYMBOL(values, location)


def white_space(char_stream, location):
    return WHITESPACE(consume(char_stream), location)


def pre_processor(char_stream, location):
    values = consume(char_stream)

    if peek(char_stream, '') == TOKENS.NUMBER_SIGN:
        return PRE_PROCESSING_SYMBOL(values + consume(char_stream), loc(values))

    while peek(char_stream, '') == ' ':
        _ = consume(char_stream)

    values += ''.join(takewhile(lambda char: char in letters, char_stream))
    if values in TOKENS.pre_processing_directives:
        return PRE_PROCESSING_SYMBOL(values, location)
    return IDENTIFIER(values, location)


def suffix(char_stream):
    return ''.join(takewhile(lambda c: c in letters, char_stream))


def number(char_stream):
    initial_char, _digits = '', digits
    if peek(char_stream) == '0':
        initial_char = consume(char_stream)
        if peek(char_stream, '') in {'x', 'X'}:
            initial_char += consume(char_stream)
            _digits = hexadecimal_digits
    return initial_char + ''.join(takewhile(lambda char: char in _digits, char_stream))


def number_literal(char_stream, location):
    values, suffix_str = number(char_stream), suffix(char_stream)

    if suffix_str and suffix_str not in possible_numeric_suffix:
        raise ValueError('{l} Invalid numeric suffix {s}'.format(l=location, s=suffix_str))

    if is_adjacent(char_stream, TOKENS.DOT, location.column_number + len(values)):
        assert not suffix_str
        return FLOAT(values + consume(char_stream) + number(char_stream), location)

    _token_type = INTEGER
    if any(imap(values.startswith, octal_prefix)) and values != '0':
        _token_type = OCTAL
    if any(imap(values.startswith, hexadecimal_prefix)):
        _token_type = HEXADECIMAL
    return _token_type(values, location, suffix_str)

escape_characters = {
    'n': '\n',
    't': '\t',
    '0': '\0',
    'f': '\f',
    'r': '\r',
    'b': '\b',
}


def string_literal(char_stream, location):
    _ = consume(char_stream)
    values = ''
    while peek(char_stream, '') != TOKENS.DOUBLE_QUOTE:
        if peek(char_stream) == '\\':
            _ = consume(char_stream)
            values += escape_characters.get(peek(char_stream), consume(char_stream))
        else:
            values += consume(char_stream)
    _ = error_if_not_value(char_stream, TOKENS.DOUBLE_QUOTE)
    return STRING(values, location)


def char_literal(char_stream, location):
    _ = consume(char_stream)  # consume initial single quote
    char = consume(char_stream)  # consume char
    if char == TOKENS.SINGLE_QUOTE:
        return CHAR('', location)

    if char == '\\':  # if char is being escaped
        token = CHAR(escape_characters.get(peek(char_stream), consume(char_stream)), location)
    else:
        token = CHAR(char, location)
    _ = error_if_not_value(char_stream, TOKENS.SINGLE_QUOTE)
    return token


def keyword_or_identifier(char_stream, location):
    values = ''.join(takewhile(lambda char: char in alpha_numeric, char_stream))
    return KEYWORD(values, location) if values in TOKENS.keyword_symbols else IDENTIFIER(values, location)


def parse(char_stream):
    return parse.rules[peek(char_stream)](char_stream, loc(peek(char_stream)))
parse.rules = dict(chain(
    izip(digits, repeat(number_literal)),
    izip(letters, repeat(keyword_or_identifier)),
    izip((s[0] for s in TOKENS.non_keyword_symbols), repeat(symbol)),
    izip(whitespace, repeat(white_space)),
    (    # override symbols " ' # .  since they require special rules.
        (TOKENS.DOUBLE_QUOTE, string_literal),
        (TOKENS.SINGLE_QUOTE, char_literal),
        (TOKENS.NUMBER_SIGN, pre_processor),

        (TOKENS.FORWARD_SLASH, comment),  # override forward slash to deal with comments // /*
    )
))


def get_directives():
    return get_directives.rules
get_directives.rules = dict(izip(parse.rules, repeat(parse)))