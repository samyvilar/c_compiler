__author__ = 'samyvilar'

from utils.sequences import peek, consume, terminal
from front_end.loader.locations import loc, LocationNotSet


def raise_error(msg='', exception_type=ValueError):
    raise exception_type(msg)


def error_if_empty(value_stream, location=LocationNotSet):
    try:
        _ = peek(value_stream)
    except StopIteration as _:
        raise_error('{l} Expected more values but got nothing'.format(v=value_stream, l=location))


def error_if_not_empty(value_stream, location=LocationNotSet):
    value = peek(value_stream, terminal)
    _ = value is not terminal and raise_error(
        '{l} Got {got} but expected nothing'.format(l=loc(value) or location, got=value)
    )


def error_if_not_value(value_stream, value, location=LocationNotSet):
    try:
        error_if_empty(value_stream, location)
    except ValueError as _:
        raise ValueError('{l} Expected {value} but got nothing'.format(l=location, value=value))

    curr = consume(value_stream)
    return (
        curr != value and raise_error('{l} Expected {value} but got {got}'.format(
            l=loc(curr or location), value=value, got=curr))) or curr


def error_if_not_type(obj_type, value_type, location=LocationNotSet):
    return (not isinstance(obj_type, value_type) and raise_error(
        '{l} Expected a value of type {t_type}, but got {got}'.format(
            l=location or loc(obj_type), t_type=value_type, got=obj_type))) or obj_type
