__author__ = 'samyvilar'

from utils.sequences import peek, consume, terminal
from front_end.loader.locations import loc, LocationNotSet


def error_if_empty(value_stream, location=LocationNotSet):
    try:
        _ = peek(value_stream)
    except StopIteration as _:
        raise ValueError('{l} Expected more values but got nothing'.format(v=value_stream, l=location))


def error_if_not_empty(value_stream, location=LocationNotSet):
    value = peek(value_stream, terminal)
    if value is not terminal:
        raise ValueError('{l} Got {got} but expected nothing'.format(l=location or loc(value), got=value))


def error_if_not_value(value_stream, value, location=LocationNotSet):
    error_if_empty(value_stream)
    curr = consume(value_stream)
    if curr != value:
        raise ValueError('{l} Expected {value} but got {got}'.format(l=location or loc(curr), value=value, got=curr))
    return curr


def error_if_not_type(obj_type, value_type, location=LocationNotSet):
    if not isinstance(obj_type, value_type):
        raise ValueError('{l} Expected a value of type {t_type}, but got {got}'.format(
            l=location or loc(obj_type), t_type=value_type, got=obj_type
        ))
    return obj_type