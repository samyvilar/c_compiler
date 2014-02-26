__author__ = 'samyvilar'

from itertools import imap

from utils.sequences import peek, peek_or_terminal
from utils.rules import rules, set_rules

from front_end.loader.locations import loc
from front_end.tokenizer.tokens import TOKENS
from front_end.parser.ast.expressions import CastExpression, CompoundLiteral
from front_end.parser.types import CType
from utils.symbol_table import push, pop

from front_end.parser.expressions.reduce import reduce_expression

from utils.errors import error_if_not_value


@reduce_expression
def cast(expr, to_type):
    return CastExpression(expr, to_type, loc(to_type))


def type_name_or_compound_literal(tokens, symbol_table):
    v, _ = symbol_table['__ type_name __'](tokens, symbol_table), error_if_not_value(tokens, TOKENS.RIGHT_PARENTHESIS)
    if peek_or_terminal(tokens) == TOKENS.LEFT_BRACE:
        v = CompoundLiteral(symbol_table['__ initializer __'](tokens, symbol_table), v, loc(v))
    return v


def type_name_or_postfix_expression(tokens, symbol_table):
    symbol_table = push(symbol_table)
    symbol_table['__ compound_literal __'] = type_name_or_compound_literal
    primary_exp = symbol_table['__ primary_expression __'](tokens, symbol_table)
    _ = pop(symbol_table)
    # pop 'type_name_or_compound_literal' and type_name_or_postfix_expression ...
    postfix_expression_rules = rules(symbol_table['__ postfix_expression __'])
    if not isinstance(primary_exp, CType):  # it must have being an expression ...
        while peek_or_terminal(tokens) in postfix_expression_rules:
            primary_exp = postfix_expression_rules[peek(tokens)](tokens, symbol_table, primary_exp)
    return primary_exp  # otherwise it must have being a type_name ...


def type_name_or_unary_expression(tokens, symbol_table):
    symbol_table = push(symbol_table)
    set_rules(type_name_or_postfix_expression, rules(symbol_table['__ postfix_expression __']))
    symbol_table['__ postfix_expression __'] = type_name_or_postfix_expression
    unary_exp = symbol_table['__ unary_expression __'](tokens, symbol_table)
    _ = pop(symbol_table)
    return unary_exp


def get_cast_expression_or_unary_expression(tokens, symbol_table):
    type_name_or_expr = type_name_or_unary_expression(tokens, symbol_table)
    return cast(cast_expression(tokens, symbol_table), type_name_or_expr) \
        if isinstance(type_name_or_expr, CType) else type_name_or_expr


@reduce_expression
def cast_expression(tokens, symbol_table):  # : '(' type_name ')' cast_expression | unary_expression
    type_name, unary_expression, postfix_expression, compound_literal = imap(
        symbol_table.__getitem__,
        ('__ type_name __', '__ unary_expression __', '__ postfix_expression __', '__ compound_literal __')
    )
    # There is a slight ambiguity here, both possible paths may begin with '('
    # unary_expression->postfix_expression->primary_expression->(compound_literal or expression)
    # both compound literals and expression may begin with '(' though compound literals are followed by a type_name
    if peek_or_terminal(tokens) == TOKENS.LEFT_PARENTHESIS:
        return get_cast_expression_or_unary_expression(tokens, symbol_table)
        # left_parenthesis, current_token = consume(tokens), peek_or_terminal(tokens)
        # if is_type_name(current_token, symbol_table):
        #     obj, _ = type_name(tokens, symbol_table), error_if_not_value(tokens, TOKENS.RIGHT_PARENTHESIS)
        #     # There is a second ambiguity between cast_expression and postfix_expression, since postfix_expression
        #     # may have compound_literal which is a cast_expression followed by an initializer_list enclosed in braces.
        #     if peek_or_terminal(tokens) == TOKENS.LEFT_BRACE:
        #         return postfix_expression(tokens, symbol_table, compound_literal(tokens, symbol_table, obj))
        #     else:
        #         return cast(cast_expression(tokens, symbol_table), obj)
        # else:
        #     # Found '(' but could not generate type_name! so we have to try unary_expression but the token stream
        #     # has already consume '(' so we have to generate the primary_expression manually, since peek/consume
        #     # reference the same token sequence and using chain would create a new token sequence ...
        #     # while we could use tee it would still consume from the original iterator, corrupting peek/consume!
        #
        #     # unary_expression -> postfix_expression -> primary_expression (postfix_expression)*
        #
        #     # This is the only way to deal with the ambiguity without modifying the token stream and
        #     # creating havoc ...
        #
        #     prim_exp = symbol_table['__ expression __'](tokens, symbol_table)
        #     _ = error_if_not_value(tokens, TOKENS.RIGHT_PARENTHESIS)
        #     return postfix_expression(tokens, symbol_table, primary_exp=prim_exp)
        #     # return unary_expression(chain((left_parenthesis,), imap(consume, repeat(tokens))), symbol_table)
    else:
        return unary_expression(tokens, symbol_table)

