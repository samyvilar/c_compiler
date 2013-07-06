__author__ = 'samyvilar'

from sequences import peek, consume
from front_end.loader.locations import loc, LocationNotSet


def error_if_empty(value_stream, location=LocationNotSet):
    try:
        _ = peek(value_stream)
    except StopIteration as _:
        raise ValueError('{l} Expected more values but got nothing'.format(v=value_stream, l=location))


def error_if_not_empty(value_stream, location=LocationNotSet):
    try:
        value = peek(value_stream)
        raise ValueError('{l} Got {got} but expected nothing'.format(l=location or loc(value), got=value))
    except StopIteration as _:
        pass


def error_if_not_value(value_stream, value, location=LocationNotSet):
    error_if_empty(value_stream)
    curr = consume(value_stream)
    if curr != value:
        raise ValueError('{l} Expected {value} but got {got}.'.format(l=location or loc(curr), value=value, got=curr))
    return curr


def error_if_not_type(value_stream, value_type, location=LocationNotSet):
    error_if_empty(value_stream)
    v = consume(value_stream)
    if not isinstance(v, value_type):
        raise ValueError('{l} Expected a value of type {t_type}, but got {got}'.format(
            l=location or loc(v), t_type=value_type, got=v
        ))
    return v


def error_if_not_lvalue(obj, oper):
    if not obj.lvalue:
        raise ValueError('{l} Operator {oper} requires an lvalue for {obj}'.format(oper=oper, obj=obj, l=loc(oper)))


def error_if_not_assignable(obj, oper):  # TODO: implement
    error_if_not_addressable(obj)
    raise NotImplementedError


def error_if_not_addressable(obj):  # TODO: implement
    raise NotImplementedError