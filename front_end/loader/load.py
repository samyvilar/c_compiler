__author__ = 'samyvilar'

from os import linesep
from StringIO import StringIO

from sequences import peek, consume
from front_end.loader.locations import Location, Str


def load(file_like):
    file_name = getattr(file_like, 'name', file_like)
    if hasattr(file_like, 'splitlines'):
        lines = file_like.splitlines(keepends=True)
    elif hasattr(file_like, 'readlines'):
        lines = file_like
    else:
        lines = open(file_like, 'r')

    def merge_lines(lines, line, file_name, line_number=1, column_number=1):
        line = enumerate(line, column_number)
        for column_number, char in line:
            if char == '\\' and linesep.startswith(peek(line, default=(0, linesep[0]))[1]):
                chars = ''.join(consume(line, default=(0, c))[1] for c in linesep)
                if chars == linesep:
                    for char in merge_lines(lines, consume(lines, default=(0, ''))[1], line_number, column_number + 1):
                        yield char
                else:
                    for column_number, char in enumerate(chars, column_number):
                        yield Str(char, Location(file_name, line_number, column_number))
            else:
                yield Str(char, Location(file_name, line_number, column_number))

    lines = enumerate(lines, 1)
    for line_number, line in lines:
        for char in merge_lines(lines, line, file_name, line_number):
            yield char


def source(file_source, file_name='__SOURCE__'):
    file_like = StringIO(file_source)
    file_like.name = file_name
    return load(file_like)