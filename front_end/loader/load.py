__author__ = 'samyvilar'

from itertools import product, ifilter, starmap, imap, repeat, count
from os import linesep, path, getcwd
from StringIO import StringIO

from front_end.loader.locations import loc
from utils.sequences import peek, consume, exhaust, takewhile
from front_end.loader.locations import Location, Str, NewLineStr


def get_repositioned_line(char_seq, location):  # get next line ...
    while not isinstance(peek(char_seq), NewLineStr):
        char = consume(char_seq)
        if char == '\\' and isinstance(peek(char_seq), NewLineStr):
            _ = exhaust(takewhile(lambda token: isinstance(token, NewLineStr), char_seq))
            for char in get_repositioned_line(char_seq, location):
                yield char
        else:
            yield Str(char, location)


def merge_lines(char_seq):
    while True:
        char = consume(char_seq)
        if char == '\\' and isinstance(peek(char_seq), NewLineStr):  # if current char is \ followed by end of line seq
            _ = exhaust(takewhile(lambda token: isinstance(token, NewLineStr), char_seq))
            for char in get_repositioned_line(char_seq, loc(char)):
                yield char
        else:
            yield char


def get_file_obj_or_error(file_name, search_paths, terminal=object()):
    present_file_name = next(ifilter(path.isfile, starmap(path.join, product(search_paths, (file_name,)))), terminal)
    if present_file_name is terminal:
        raise ValueError('Could not locate file {0}'.format(file_name))
    return open(present_file_name, 'rb')


def get_newline_if_possible(char_seq):
    return ''.join(takewhile(
        lambda c, new_line=iter(linesep), _seq=char_seq: c == next(new_line) and (consume(_seq) or 1),
        imap(peek, repeat(char_seq))
    ))


def positioned_chars(char_seq, file_name, initial_line_number=1, initial_column_number=1):
    line_numbers, column_numbers = imap(count, (initial_line_number, initial_column_number))
    line_number = next(line_numbers)
    for ch in imap(peek, repeat(char_seq)):
        if linesep.startswith(ch):  # check for an end of line sequence ...
            possible_end_of_lines_chars = get_newline_if_possible(char_seq)  # get possible end of line sequence
            str_type = NewLineStr if possible_end_of_lines_chars == linesep else Str
            for c in possible_end_of_lines_chars:  # emit sequence ...
                yield str_type(c, Location(file_name, line_number, next(column_numbers)))
            if str_type is NewLineStr:  # if sequence is end of line then reset column # and inc line #
                column_numbers, line_number = count(initial_column_number), next(line_numbers)
        else:
            yield Str(consume(char_seq), Location(file_name, line_number, next(column_numbers)))


def load(file_like_or_file_name, search_paths=(getcwd(),)):
    file_name = getattr(file_like_or_file_name, 'name', file_like_or_file_name)
    if not hasattr(file_like_or_file_name, 'read'):
        file_like_or_file_name = get_file_obj_or_error(file_like_or_file_name, search_paths)
    chars = positioned_chars(iter(file_like_or_file_name.read()), file_name)
    _ = getattr(file_like_or_file_name, 'close', lambda: None)()
    return merge_lines(chars)


def source(file_source, file_name='__SOURCE__'):
    file_like = StringIO(file_source)
    file_like.name = file_name
    return load(file_like)