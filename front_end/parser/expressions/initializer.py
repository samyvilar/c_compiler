__author__ = 'samyvilar'

from itertools import imap, chain, izip, repeat, takewhile, starmap

from utils.sequences import peek, consume, peek_or_terminal, exhaust
from utils.rules import set_rules, rules, identity

from front_end.loader.locations import loc, EOFLocation
from front_end.tokenizer.tokens import TOKENS, IDENTIFIER
from front_end.parser.ast.expressions import exp, EmptyExpression, Initializer
from front_end.parser.ast.expressions import IdentifierDesignatedExpression
from front_end.parser.ast.expressions import RangeDesignatedExpression, OffsetDesignatedExpression
from front_end.parser.ast.expressions import NumericalDesignation, designation, DesignatedExpression
from front_end.parser.ast.expressions import DefaultOffsetDesignationExpression, ConstantExpression

from front_end.parser.types import StructType, ArrayType, UnionType
from front_end.parser.types import suggested_size, c_type, scalar_types, safe_type_coercion, members, offset

from front_end.parser.expressions.cast import cast

from utils.errors import error_if_not_value, error_if_not_type, raise_error

from logging_config import logging


logger = logging.getLogger('parser')


def range_designated_expr(start, tokens, symbol_table):
    constant_expression = symbol_table['__ constant_expression __']
    end = error_if_not_value(tokens, TOKENS.ELLIPSIS) and NumericalDesignation(
        exp(constant_expression(tokens, symbol_table))
    )
    return error_if_not_value(tokens, TOKENS.RIGHT_BRACKET) and RangeDesignatedExpression(
        start, end, _expr_or_designated_expr(tokens, symbol_table), loc(end)
    )


def offset_designated_expr(tokens, symbol_table):  # '[' positive_integral (... positive_integral)? ']'
    constant_expression = error_if_not_value(tokens, TOKENS.LEFT_BRACKET) and symbol_table['__ constant_expression __']
    designation = NumericalDesignation(exp(constant_expression(tokens, symbol_table)))

    if peek_or_terminal(tokens) == TOKENS.ELLIPSIS:
        return range_designated_expr(designation, tokens, symbol_table)

    return error_if_not_value(tokens, TOKENS.RIGHT_BRACKET) and OffsetDesignatedExpression(
        designation, _expr_or_designated_expr(tokens, symbol_table)
    )


def identifier_designated_expr(tokens, symbol_table):  # '.'IDENTIFIER
    identifier = error_if_not_value(tokens, TOKENS.DOT) and error_if_not_type(consume(tokens), IDENTIFIER)
    return IdentifierDesignatedExpression(identifier, _expr_or_designated_expr(tokens, symbol_table), loc(identifier))


def _assignment_expr(tokens, symbol_table):
    return symbol_table['__ assignment_expression __'](tokens, symbol_table)


def _initializer(tokens, symbol_table):
    return symbol_table['__ initializer __'](tokens, symbol_table)


def _assignment_expression_or_initializer(tokens, symbol_table):
    return error_if_not_value(tokens, TOKENS.EQUAL) and rules(
        _assignment_expression_or_initializer
    )[peek_or_terminal(tokens)](tokens, symbol_table)
set_rules(_assignment_expression_or_initializer, ((TOKENS.LEFT_BRACE, _initializer),), _assignment_expr)


def _expr_or_designated_expr(tokens, symbol_table):
    return rules(_expr_or_designated_expr)[peek_or_terminal(tokens)](tokens, symbol_table)
set_rules(
    _expr_or_designated_expr,
    (
        (TOKENS.DOT, identifier_designated_expr),
        (TOKENS.LEFT_BRACKET, offset_designated_expr),
        (TOKENS.EQUAL, _assignment_expression_or_initializer)
    )
)


def designated_expression(tokens, symbol_table):  # (offset or range or identifier)+ = assignment_expression
    return rules(designated_expression)[peek(tokens)](tokens, symbol_table)
set_rules(designated_expression, ((TOKENS.LEFT_BRACKET, offset_designated_expr), (TOKENS.DOT, identifier_designated_expr)))


def designated_expression_or_expression(tokens, symbol_table):
    # ((designation '=')? (assignment_expression or initializer))
    return rules(designated_expression).get(
        peek_or_terminal(tokens),
        symbol_table['__ assignment_expression __']
    )(tokens, symbol_table)


def initializer_list(tokens, symbol_table):
    return () if peek(tokens, TOKENS.RIGHT_BRACE) == TOKENS.RIGHT_BRACE else chain(
        (designated_expression_or_expression(tokens, symbol_table),),
        starmap(
            designated_expression_or_expression,
            takewhile(
                lambda i: peek_or_terminal(i[0]) == TOKENS.COMMA and consume(i[0])
                and peek(tokens, TOKENS.RIGHT_BRACE) != TOKENS.RIGHT_BRACE,
                repeat((tokens, symbol_table))
            )
        )
    )


def initializer(tokens, symbol_table):  # '{' initializer* '}'
    location = loc(error_if_not_value(tokens, TOKENS.LEFT_BRACE))
    values = Initializer(enumerate(initializer_list(tokens, symbol_table)), None, location)
    return error_if_not_value(tokens, TOKENS.RIGHT_BRACE) and values


# Verify Initializer ..........

def _size(ctype):
    return rules(_size)[type(ctype)](ctype)
set_rules(
    _size,
    chain(
        izip(scalar_types, repeat(suggested_size)),
        (
            (ArrayType, lambda ctype: len(ctype) * _size(c_type(ctype))),
            (UnionType, lambda ctype: _size(max_type(imap(c_type, members(ctype))))),
            (StructType, lambda ctype: sum(imap(_size, imap(c_type, members(ctype)))))
        ),
    ),
)


def max_type(ctypes):
    return max(ctypes, key=_size)


def initializer_defaults(ctype):
    return Initializer(enumerate(rules(initializer_defaults)[type(ctype)](ctype)), ctype, loc(c_type))
set_rules(
    initializer_defaults,
    chain(
        izip(scalar_types, repeat(lambda ctype: (EmptyExpression(ctype, loc(ctype)),))),
        (
            (ArrayType, lambda ctype: imap(initializer_defaults, repeat(c_type(ctype), ctype.length or 0))),
            (StructType, lambda ctype: imap(initializer_defaults, imap(c_type, members(ctype)))),
            (UnionType, lambda ctype: (initializer_defaults(max_type(imap(c_type, members(ctype)))),)),
        )
    ),
)


def parse_initializer(expr, declaration):
    return set_default_initializer(expr, initializer_defaults(c_type(declaration)))  # create and update initializer ...


def parse_range_designated_expr(desig_expr, default_values):
    first, last = designation(desig_expr)
    exhaust(
        imap(
            parse_designated_expr,
            imap(OffsetDesignatedExpression, xrange(first, last + 1), repeat(exp(desig_expr)), repeat(loc(desig_expr))),
            repeat(default_values)
        )
    )


def parse_identifier_designated_expr(desig_expr, default_values):
    return parse_designated_expr(
        OffsetDesignatedExpression(
            offset(c_type(default_values), designation(desig_expr)),  # get offset ...
            exp(desig_expr),
            loc(desig_expr)
        ),
        default_values
    )


def update_scalar_type_initializer(desig_expr, default_values):
    assert len(default_values) == 1
    expr, desig = exp(desig_expr), designation(desig_expr, 0)
    if desig != 0:
        logger.warning('Excess Elements in initializer ...')
    else:
        default_values[0] = cast(expr, c_type(default_values[0]))


def update_composite_type_initializer(desig_expr, default_values):
    desig = designation(desig_expr)
    if desig > default_values:
        logger.warning('Excess elements in initializer ...')
    else:
        assert len(default_values[desig]) == 1
        default_values[desig][0] = cast(exp(desig_expr), c_type(default_values[desig][0]))


def update_default_value(desig_expr, default_values):
    ctype, desig, expr = c_type(default_values), designation(desig_expr), exp(desig_expr)
    if desig >= len(default_values):
        logger.warning(
            '{0} Excess element {1} {2} in initializer, it will be ignored ... '.format(
                loc(desig_expr), desig, expr
            ))
    else:
        _ = (not safe_type_coercion(c_type(expr), c_type(default_values.get(desig)))) and raise_error(
            '{l} Unable to coerce from {f} to {t}'.format(l=loc(expr), f=c_type(expr), t=c_type(default_values[desig]))
        )
        update_func = update_composite_type_initializer \
            if isinstance(ctype, (StructType, ArrayType)) else update_scalar_type_initializer
        update_func(desig_expr, default_values)


def parse_designated_union_expr(desig_expr, default_values):
    # care must be taken when dealing with union initializer, they may only set a single expression ...
    ctype, desig, expr = c_type(default_values), designation(desig_expr), exp(desig_expr)

    if isinstance(expr, DesignatedExpression):
        parse_designated_expr(expr, default_values)
    elif isinstance(expr, Initializer):
        set_default_initializer(expr, default_values)
    else:
        default_values[0] = expr


def parse_default_offset_designated_expr(desig_expr, default_values):
    ctype, desig, expr = c_type(default_values), designation(desig_expr), exp(desig_expr)

    if isinstance(expr, DesignatedExpression) and error_if_not_type(ctype, (StructType, ArrayType)):
        parse_designated_expr(expr, default_values[desig])
    elif isinstance(expr, Initializer):
        default_values = default_values[desig] if isinstance(ctype, (StructType, ArrayType)) else default_values
        set_default_initializer(expr, default_values)
    else:
        update_default_value(desig_expr, default_values)


def parse_offset_designated_expr(desig_expr, default_values):
    return rules(parse_offset_designated_expr)[type(c_type(default_values))](desig_expr, default_values)
set_rules(
    parse_offset_designated_expr,
    (
        (UnionType, parse_designated_union_expr),
    ),
    parse_default_offset_designated_expr
)


def max_designation_mag(desig_expr):
    return rules(max_designation_mag)[type(desig_expr)](designation(desig_expr))
set_rules(
    max_designation_mag,
    (
        (DefaultOffsetDesignationExpression, identity),
        (OffsetDesignatedExpression, identity),
        (RangeDesignatedExpression, max)
    )
)


def expand_defaults(desig_expr, default_values):
    desig, ctype = max_designation_mag(desig_expr), c_type(default_values)
    length_diff = getattr(ctype, 'length', 0) is None and (desig - len(default_values) + 1)
    _ = length_diff > 0 and default_values.update(  # expand defaults if incomplete ArrayType ...
        enumerate(initializer_defaults(ArrayType(ctype, length_diff)), length_diff + 1))


def initializer_desig_exprs(initializer, default_values):
    previous_desig_offset_mag = -1
    for expr_or_desig_expr in initializer.itervalues():
        if not isinstance(expr_or_desig_expr, DesignatedExpression):  # assign default designation if none present ...
            expr_or_desig_expr = DefaultOffsetDesignationExpression(
                previous_desig_offset_mag + 1,  # use previous designation ...
                expr_or_desig_expr,
                loc(expr_or_desig_expr)
            )
        elif isinstance(expr_or_desig_expr, IdentifierDesignatedExpression):  # if designation is an identifier
            expr_or_desig_expr = OffsetDesignatedExpression(
                offset(c_type(default_values), designation(expr_or_desig_expr)),  # get offset ...
                exp(expr_or_desig_expr),
                loc(expr_or_desig_expr)
            )

        expand_defaults(expr_or_desig_expr, default_values)  # expand defaults for incomplete array types

        yield expr_or_desig_expr
        previous_desig_offset_mag = max_designation_mag(expr_or_desig_expr)  # record designation in case we need new 1


def parse_designated_expr(desig_expr, default_values):
    rules(parse_designated_expr)[type(desig_expr)](desig_expr, default_values)
set_rules(
    parse_designated_expr,
    (
        (IdentifierDesignatedExpression, parse_identifier_designated_expr),
        (OffsetDesignatedExpression, parse_offset_designated_expr),
        (DefaultOffsetDesignationExpression, parse_offset_designated_expr),
        (RangeDesignatedExpression, parse_range_designated_expr)
    ),
)


def set_default_initializer(initializer, default_values):
    # Complete ArrayTypes with initializer containing a single non designated expression assign the value through out
    if isinstance(c_type(default_values), ArrayType) \
            and not isinstance(initializer[0], DesignatedExpression) \
            and len(initializer) == 1 \
            and c_type(default_values).length is not None:
        initializer = Initializer(
            enumerate(repeat(initializer[0], len(c_type(default_values)))),
            c_type(default_values)(loc(initializer)),
            loc(initializer)
        )
    exhaust(imap(parse_designated_expr, initializer_desig_exprs(initializer, default_values), repeat(default_values)))
    return default_values