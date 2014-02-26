__author__ = 'samyvilar'

from itertools import chain, izip, repeat, imap, starmap

from utils.rules import rules, set_rules
from utils.sequences import peek, consume, peek_or_terminal, terminal, takewhile, exhaust

from front_end.loader.locations import loc, EOFLocation, line_number
from front_end.tokenizer.tokens import TOKENS, SYMBOL, KEYWORD, IDENTIFIER, FLOAT, INTEGER, STRING, CHAR, WHITESPACE
from front_end.tokenizer.tokens import HEXADECIMAL, OCTAL
from front_end.tokenizer.tokens import PRE_PROCESSING_SYMBOL, letters, alpha_numeric, whitespace
from front_end.tokenizer.tokens import digits, hexadecimal_digits, hexadecimal_prefix, octal_prefix, digit
from front_end.tokenizer.tokens import possible_numeric_suffix
from front_end.tokenizer.tokens import SINGLE_LINE_COMMENT, MULTI_LINE_COMMENT

from utils.errors import error_if_not_value, raise_error


def get_line(values):  # get all the tokens on the current line, being that preprocessor works on a line-by-line basis
    return takewhile(
        lambda token, initial_line_number=line_number(peek(values)): initial_line_number == line_number(token),
        values
    ) if peek_or_terminal(values) is not terminal else iter(())


def single_line_comment(char_stream, location):
    return SINGLE_LINE_COMMENT(''.join(get_line(char_stream)), location)


def multi_line_comment(char_stream, location):
    def _values(char_stream):
        while peek_or_terminal(char_stream) is not terminal:
            current_value = consume(char_stream)
            yield current_value
            # we have consumed a star check if its adjacent value is a forward slash if it is consume and break
            if current_value == TOKENS.STAR and peek_or_terminal(char_stream) == TOKENS.FORWARD_SLASH:
                yield consume(char_stream)
                break
    _comment = ''.join(_values(char_stream))
    if _comment.endswith(TOKENS.END_OF_MULTI_LINE_COMMENT):
        return MULTI_LINE_COMMENT(''.join(_comment), location)
    raise_error('{l} Could no locate end of multi-line comment.'.format(l=location))


def comment(char_stream, location):  # all comments start with a FORWARD_SLASH ...
    _symbol = symbol(char_stream, location)
    return rules(comment).get(_symbol, lambda _, __, s=_symbol: s)(char_stream, location)
set_rules(
    comment,
    (
        (TOKENS.START_OF_COMMENT, single_line_comment),
        (TOKENS.START_OF_MULTI_LINE_COMMENT, multi_line_comment)
    )
)


def is_value_adjacent(values, current_location, value):
    next_value = peek_or_terminal(values)
    next_location = loc(next_value, EOFLocation)
    return not any(
        starmap(
            cmp,
            izip(
                (value,      current_location.line_number, current_location.column_number + len(value)),
                (next_value, next_location.line_number,     next_location.column_number)
            )
        )
    )


def symbol(char_stream, location):
    def _values(char_stream):
        value = ''
        while value + peek(char_stream) in TOKENS.non_keyword_symbols:
            current_value = consume(char_stream)
            value += current_value
            yield current_value
    value = ''.join(_values(char_stream))
    next_char = peek_or_terminal(char_stream)
    # if value is a single dot check if the next value is a number for possible float or ellipsis ...
    if value == TOKENS.DOT and next_char is not terminal:
        if next_char in digits:  # check for float ...
            return FLOAT(value + number(char_stream), location)
        if next_char == TOKENS.DOT:  # check for ellipsis ...
            value += consume(char_stream)
            if peek_or_terminal(char_stream) == TOKENS.DOT:
                return SYMBOL(value + consume(char_stream), location)  # TOKENS.ELLIPSIS
            raise_error('{l} Unable to tokenize: `{t}`'.format(l=location, t=TOKENS.DOT + TOKENS.DOT))
    return SYMBOL(value, location)


def white_space(char_stream, location):
    return WHITESPACE(consume(char_stream), location)


def pre_processor(char_stream, location):  # returns pre_processing symbol or #identifier ...
    values = consume(char_stream)
    if peek_or_terminal(char_stream) == TOKENS.NUMBER_SIGN:  # token concatenation symbol ...
        values += consume(char_stream)
    else:
        _ = exhaust(takewhile({' ', '\t', '\a'}.__contains__, char_stream))
        values += ''.join(takewhile(letters.__contains__, char_stream))
    return rules(pre_processor).get(values, IDENTIFIER)(values, location)
set_rules(pre_processor, izip(TOKENS.pre_processing_directives, repeat(PRE_PROCESSING_SYMBOL)))


def suffix(char_stream):
    return ''.join(takewhile(letters.__contains__, char_stream))


def number(char_stream, hexadecimal_chars={'x', 'X'}):
    initial_char, _digits = '', digits
    if peek_or_terminal(char_stream) == digit(0):
        initial_char = consume(char_stream)
        if peek_or_terminal(char_stream) in hexadecimal_chars:
            initial_char += consume(char_stream)
            _digits = hexadecimal_digits
    return initial_char + ''.join(takewhile(_digits.__contains__, char_stream))


def number_literal(char_stream, location):
    values, sfix = number(char_stream), suffix(char_stream)
    _ = sfix not in possible_numeric_suffix and raise_error('{0} Invalid numeric suffix {1}'.format(location, sfix))

    if peek_or_terminal(char_stream) == TOKENS.DOT:
        return FLOAT(values + consume(char_stream) + number(char_stream), location)

    _token_type = INTEGER
    if any(imap(values.startswith, octal_prefix)) and values != digit(0):
        _token_type = OCTAL
    if any(imap(values.startswith, hexadecimal_prefix)):
        _token_type = HEXADECIMAL
    return _token_type(values, location, sfix)

escape_characters = {
    'n': '\n',
    't': '\t',
    '0': '\0',
    'f': '\f',
    'r': '\r',
    'b': '\b',
}


def string_literal(char_stream, location):
    def _values(char_stream):
        while peek(char_stream, TOKENS.DOUBLE_QUOTE) != TOKENS.DOUBLE_QUOTE:
            value = consume(char_stream)
            value = escape_characters.get(peek(char_stream), consume(char_stream)) if value == '\\' else value
            yield value
        _ = error_if_not_value(char_stream, TOKENS.DOUBLE_QUOTE)
    return consume(char_stream) and STRING(''.join(_values(char_stream)), location)


def char_literal(char_stream, location):
    char = consume(char_stream) and consume(char_stream)  # consume initial single quote, consume char
    if char == TOKENS.SINGLE_QUOTE:  # empty char ...
        return CHAR('', location)
    if char == '\\':  # if char is being escaped
        char = escape_characters.get(peek(char_stream), consume(char_stream))
    return error_if_not_value(char_stream, TOKENS.SINGLE_QUOTE) and CHAR(char, location)


def keyword_or_identifier(char_stream, location):
    values = ''.join(takewhile(alpha_numeric.__contains__, char_stream))
    return rules(keyword_or_identifier).get(values, IDENTIFIER)(values, location)
set_rules(keyword_or_identifier, izip(TOKENS.keyword_symbols, repeat(KEYWORD)))


def no_rule(char_stream, location):
    raise_error('{l} Unable to tokenize {c}'.format(l=location, c=peek(char_stream)))


def parse(char_stream):
    return rules(parse)[peek(char_stream)](char_stream, loc(peek(char_stream)))
set_rules(
    parse,
    chain(
        izip(digits, repeat(number_literal)),
        izip(letters, repeat(keyword_or_identifier)),
        izip(imap(next, imap(iter, TOKENS.non_keyword_symbols)), repeat(symbol)),
        izip(whitespace, repeat(white_space)),
        (    # override symbols the following symbols, since they require special rules. ...
            (TOKENS.DOUBLE_QUOTE, string_literal),
            (TOKENS.SINGLE_QUOTE, char_literal),
            (TOKENS.NUMBER_SIGN, pre_processor),
            (TOKENS.FORWARD_SLASH, comment),  # override forward slash to deal with comments SINGLE and MULTI-LINE ...
        )
    ),
    no_rule
)


def get_directives():
    return rules(get_directives)
set_rules(get_directives, (), parse)