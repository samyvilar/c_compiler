__author__ = 'samyvilar'

import os

from front_end import List
from front_end.loader import logger
from front_end.loader.locations import Location, loc, set_locations, Str
from logging_config import logging


def load_file(file_like=None, source=None):
    if file_like is not None and source is not None:
        file_name, file_source = file_like, source
    elif file_like and source is None:
        if hasattr(file_like, 'read'):
            file_name, file_source = str(file_like), file_like.read()
        else:
            if not os.path.isfile(file_like):
                raise ValueError('Could not locate file {f}.'.format(f=file_like))
            file_name, file_source = file_like, open(file_like, 'r').read()
    elif source:
        file_name, file_source = file_like, source
    else:
        raise ValueError('{f} Could not be loaded, giving source {s}'.format(
            f=file_like,
            s=source and source[:10] + ('...' if source and len(source) > 10 else '')
        ))

    file_source = file_source if os.linesep == '\n' else file_source.replace(os.linesep, '\n')
    # replace system line separator by newline since some systems used 2 chars to indicate new line.
    logger.debug('Opened/read/modified {size} bytes, with system newline {n}'.format(
        n=repr(os.linesep), size=len(file_source)), extra={'location': file_name})
    return file_name, file_source


def parse_single_line_comment(char_stream):
    tokens, location = [], loc(char_stream[0])
    # while we are in the same line, leave the new line char as a whitespace, if it exists.
    while char_stream and char_stream[0] != '\n' and loc(char_stream[0]).line_number == location.line_number:
        tokens.append(char_stream.pop(0))
    return tokens


def parse_multi_line_comment(char_stream):
    saw_star, found, tokens, location = False, False, [], loc(char_stream[0])
    while char_stream and not found:
        tokens.append(char_stream.pop(0))
        if tokens[-1] == '*':
            saw_star = True
        elif tokens[-1] == '/':
            if saw_star:
                found = True
            else:
                saw_star = False
        else:
            saw_star = False
    if found:
        return tokens
    raise ValueError('{l} Did not locate end of multi-line comment.'.format(l=location))


def strip(char_seq):  # strip leading and trailing spaces.
    while char_seq and char_seq[0] == ' ':  # remove leading blanks.
        _ = char_seq.pop(0)

    while char_seq and char_seq[-1] == ' ':  # remove trailing blanks.
        _ = char_seq.pop()


def initial_processing(char_seq):  # remove comments, leading and trailing spaces.
    count, new_char_array = 0, []

    while char_seq:
        token = char_seq.pop(0)
        if char_seq and token == char_seq[0] == '/':  # single line comment.
            _ = parse_single_line_comment(char_seq)
            count += 1
        elif char_seq and token == '/' and char_seq[0] == '*':  # multi-line comment.
            location = loc(token)
            _ = parse_multi_line_comment(char_seq)
            new_char_array.append(Str(' ', location))  # replace multi-line with single space.
            count += 1
        else:
            new_char_array.append(token)

    strip(new_char_array)
    _ = count and logging.debug('Removed {c} comments'.format(c=count),
                                extra={'location': loc(new_char_array[0]).file_name})
    return new_char_array


def get_lines(char_seq, new_line_char='\n'):
    lines = [[]]
    while char_seq:
        lines[-1].append(char_seq.pop(0))
        if char_seq and lines[-1][-1] == new_line_char:  # guarantees that lines have at least one char the newline ch.
            lines.append([])
    return [] if lines == [[]] else lines


def merge_lines(char_seq):  # merge lines ending with \ and renumber only those characters.
    count, new_char_array, lines = 0, [], get_lines(char_seq)  # split char sequence into lines.

    while lines:
        line = lines.pop(0)
        new_line = line and line[-1] == '\n' and line.pop()
        while line and line[-1] == '\\':  # check that this line ends with back slash.
            back_slash = line.pop()  # remove back slash char
            count += 1
            l = lines and lines.pop(0)  # get the next line
            _ = l and l[-1] == '\n' and l.pop()
            for ch in l:  # renumber all the chars of the next line.
                line.append(Str(
                    ch,
                    Location(
                        loc(ch).file_name,
                        loc(back_slash).line_number,
                        loc(back_slash).column_number + loc(ch).column_number - 1  # minus one since we start from 1.
                    )
                ))

        if new_line:
            line.append(Str(
                '\n',
                Location(loc(line[-1]).file_name, loc(line[-1]).line_number, loc(line[-1]).column_number + 1) if line
                else loc(new_line)
            ))
        new_char_array.extend(line)

    _ = count and new_char_array and logger.debug('{l} Merged {n} lines.'.format(
        n=count, l=loc(new_char_array[0]).file_name
    ))
    return new_char_array


class Load(List):
    def __init__(self, file_like=None, source=None):
        if file_like is None and source is None:
            super(Load, self).__init__(())
        else:                                  # load file, replace system new line with '\n'
            self.file_name, self.file_source = load_file(file_like, source)
            # merge lines, remove comments.
            super(Load, self).__init__(
                initial_processing(
                    merge_lines(
                        set_locations(self.file_name, self.file_source)
                    )
                )
            )