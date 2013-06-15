__author__ = 'samyvilar'

from front_end import consumed
from front_end.loader.locations import loc, LocationNotSet

from front_end.parser.ast.expressions import lvalue


def error_if_empty(value_stream, location=LocationNotSet):
    if not value_stream:
        c = consumed(value_stream)
        raise ValueError('{l} Expected more values but got nothing, {v}'.format(
            v=value_stream, l=location or c and loc(c[-1])
        ))


def error_if_not_empty(value_stream, location=LocationNotSet):
    if value_stream:
        raise ValueError('{l} Got {got} but expected nothing'.format(
            l=location or loc(value_stream[0]), got=value_stream[0]
        ))


def error_if_not_value(value_stream, value, location=LocationNotSet):
    error_if_empty(value_stream)
    v = value_stream.pop(0)
    if v != value:
        raise ValueError('{l} Expected {value} but got {got}.'.format(l=location or loc(v), value=value, got=v))
    return v


def error_if_not_any_value(value_stream, values, location=LocationNotSet):
    error_if_empty(value_stream)
    v = value_stream.pop(0)
    if v not in values:
        raise ValueError('{l} Expected one of {values} got {got}.'.format(l=location or loc(v), got=v, values=values))
    return v


def error_if_not_type(value_stream, value_type, location=LocationNotSet):
    error_if_empty(value_stream)
    v = value_stream.pop(0)
    if not isinstance(v, value_type):
        raise ValueError('{l} Expected a value of type {t_type}, but got {got}'.format(
            l=location or loc(v), t_type=value_type, got=v
        ))
    return v


def error_if_not_lvalue(obj, oper):
    if not lvalue(obj):
        raise ValueError('{l} Operator {oper} requires an lvalue for {obj}'.format(oper=oper, obj=obj, l=loc(oper)))