__author__ = 'samyvilar'


from itertools import chain, imap, izip_longest, repeat, ifilterfalse
from collections import Iterable, deque

from utils import __required__

__iterators__ = {}
terminal = object()


def peek_or_terminal(seq):
    return peek(seq, terminal)


def peek(seq, default=__required__):
    if seq in __iterators__:
        return __iterators__[seq]
    try:
        __iterators__[seq] = next(seq)
        return __iterators__[seq]
    except StopIteration as ex:
        if default is __required__:
            raise ex
        return default


def consume(seq, default=__required__):
    if seq in __iterators__:
        return __iterators__.pop(seq)

    try:
        return next(seq)
    except StopIteration as ex:
        if default is __required__:
            raise ex
        return default


def exhaust(iterator):
    _ = deque(iterator, maxlen=0)


def consume_all(*values):
    for value in values:
        for v in imap(consume, repeat(value)):
            yield v


def takewhile(func, value_stream):
    value_stream = iter(value_stream)
    func = func or (lambda _: _)
    while func(peek(value_stream)):
        yield consume(value_stream)


def reverse(values):
    values = iter(values)
    for value in chain(reverse(values), (next(values),)):
        yield value


def flatten(values):
    if isinstance(values, Iterable):
        for v in chain.from_iterable(imap(flatten, values)):
            yield v
    else:
        yield values


def permute_case(s, index=0):
    # Permute the case of each char of a giving string ... '' -> ('',) 'a' -> ('a', 'A') 'ab' -> 'ab', 'Ab', 'aB', 'AB'
    return (len(s) > 1 and chain.from_iterable(
        (prefix + s[index] + postfix, prefix + s[index].upper() + postfix)
        for prefix, postfix in izip_longest(
            permute_case(s[0:index], index + 1),
            permute_case(s[index + 1:], index + 1),
            fillvalue=''
        )
    )) or (s and (s, s.upper())) or (s,)


default_last_object = __required__


__terminal__ = object()


def all_but_last(values, assert_last=default_last_object, location=''):
    temp = next(values, __terminal__)

    if temp is __terminal__ and not assert_last:
        raise ValueError('{l} Expected at least {e} but got empty generator ...'.format(l=location, e=assert_last))

    for v in values:
        yield temp
        temp = v

    if assert_last is not default_last_object and not isinstance(temp, assert_last):
        raise ValueError('{l} Expected {e} but got {g}'.format(l=location, e=assert_last, g=temp))