__author__ = 'samyvilar'

from itertools import chain

values = {}


def peek(seq, **kwargs):
    if hasattr(seq, '__getitem__'):
        return seq[0] if seq else (kwargs['default'] if 'default' in kwargs else seq[0])

    if seq not in values:
        try:
            values[seq] = next(seq)
        except StopIteration as ex:
            if 'default' in kwargs:
                return kwargs['default']
            raise ValueError('Empty Sequence!')
    return values[seq]


def consume(seq, **kwargs):
    if hasattr(seq, 'pop'):
        return seq.pop(0) if seq else (kwargs['default'] if 'default' in kwargs else seq.pop(0))

    if seq not in values:
        return next(seq, kwargs['default']) if 'default' in kwargs else next(seq)
    else:
        return values.pop(seq)


def takewhile(func, value_stream):
    terminal = object()
    while peek(value_stream, default=terminal) is not terminal and func(peek(value_stream)):
        yield consume(value_stream)


def reverse(values):
    values = iter(values)
    for value in chain(reverse(values), (next(values),)):
        yield value