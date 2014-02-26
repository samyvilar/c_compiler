__author__ = 'samyvilar'

from front_end.loader.locations import loc
from front_end.parser.ast.expressions import IdentifierExpression, ConstantExpression, exp


def constant_expression(tokens, symbol_table):
    _exp = symbol_table['__ logical_or_expression __'](tokens, symbol_table)

    # ENUM types ...
    if isinstance(_exp, IdentifierExpression) and isinstance(symbol_table.get(exp(_exp), type), ConstantExpression):
        _exp = symbol_table[exp(_exp)]

    if not isinstance(_exp, ConstantExpression):
        raise ValueError('{l} Expected a constant expression got {got}'.format(l=loc(_exp), got=_exp))
    return _exp
