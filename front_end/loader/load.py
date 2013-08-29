__author__ = 'samyvilar'


from os import linesep, path, getcwd
from StringIO import StringIO

from sequences import peek, consume
from front_end.loader.locations import Location, Str


def load(file_like, search_paths=(getcwd(),)):
    file_name = getattr(file_like, 'name', file_like)

    if hasattr(file_like, 'readlines'):
        lines = file_like
    else:
        if path.isfile(file_like):
            lines = open(file_like, 'r')
        else:
            lines = None
            for d in search_paths:
                if path.isfile(path.join(d, file_like)):
                    lines = open(path.join(d, file_like), 'r')
                    break

    if lines is None:
        raise ValueError('Could not locate file {f}'.format(f=file_like))

    def merge_lines(lines, line, file_name, line_number=1, column_number=1):
        line = enumerate(line, column_number)
        while peek(line, ''):
            column_number, char = consume(line)
            if char == '\\' and linesep.startswith(peek(line, (0, linesep[0]))[1]):
                chars = ''.join(consume(line, default=(0, c))[1] for c in linesep)
                if chars == linesep:
                    for char in merge_lines(lines, consume(lines, default=(0, ''))[1], file_name,
                                            line_number=line_number, column_number=column_number + 1):
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
    _ = getattr(lines, 'close', lambda: None)()


def source(file_source, file_name='__SOURCE__'):
    file_like = StringIO(file_source)
    file_like.name = file_name
    return load(file_like)