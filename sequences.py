__author__ = 'samyvilar'

from itertools import chain, imap, izip_longest
from collections import Iterable

__iterators__ = {}

__required__ = object()
terminal = object()


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


def takewhile(func, value_stream):
    value_stream = iter(value_stream)
    func = func or (lambda _: True)
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


default_last_object = object()


def all_but_last(values, assert_last=default_last_object, location=''):
    temp = next(values)
    for v in values:
        yield temp
        temp = v

    if assert_last is not default_last_object and not isinstance(temp, assert_last):
        raise ValueError('{l}Expected but got {g}'.format(l=location + ' ', g=temp))

