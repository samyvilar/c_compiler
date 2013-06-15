__author__ = 'samyvilar'

from front_end.loader.locations import loc
from front_end.tokenizer.tokenize import Tokenize, line_tokens
from front_end.tokenizer.tokens import TOKENS, IDENTIFIER
from front_end.parser.expressions.expression import constant_expression
from front_end.tokenizer.tokens import INTEGER
from front_end.errors import error_if_not_value


def expand(arguments, macros):
    args = Tokenize()
    while arguments:
        arg = arguments.pop(0)
        if isinstance(arg, IDENTIFIER):
            args.extend(macros.get(arg, INTEGER('0', loc(arg)), arguments))
        else:
            args.append(arg)
    return args


def evaluate_expression(arguments, macros):
    arguments = expand(arguments, macros)
    exp = constant_expression(arguments, {})
    return exp.exp


def get_body(all_tokens, location):
    block_level, body, found = 0, Tokenize(), False
    while all_tokens:
        if all_tokens[0] in {TOKENS.PELIF, TOKENS.PELSE, TOKENS.PENDIF} and not block_level:
            found = True
            break
        if all_tokens[0] in {TOKENS.PIF, TOKENS.PIFDEF, TOKENS.PIFNDEF}:
            block_level += 1
        if all_tokens[0] == TOKENS.PENDIF and block_level:
            block_level -= 1
        body.append(all_tokens.pop(0))
    if not found:
        raise ValueError('{l}, Could not locate end of body for #if statement'.format(l=location))
    return body


class IFBlock(object):
    def __init__(self, all_tokens, macros, new_tokens, line, current_token):
        self.location = loc(current_token)
        self.arguments = line
        self.body, self.blocks = get_body(all_tokens, loc(current_token)), [self]

        while all_tokens[0] == TOKENS.PELIF:
            self.blocks.append(ELIFBlock(all_tokens))

        if all_tokens[0] == TOKENS.PELSE:
            self.blocks.append(ElseBlock(all_tokens))

        _ = error_if_not_value(all_tokens, TOKENS.PENDIF)

    @property
    def arguments(self):
        return self._arguments

    @arguments.setter
    def arguments(self, values):
        if not values:
            raise ValueError('{l} {block} has no expression.'.format(
                l=loc(self), block=self.__class__.__name__
            ))
        self._arguments = values

    def evaluate(self, macros):
        for block in self.blocks:
            if block.is_true(macros):
                return block.body
        return Tokenize()

    def is_true(self, macros):
        return evaluate_expression(self.arguments, macros)


class ELIFBlock(IFBlock):
    # noinspection PyMissingConstructor
    def __init__(self, all_tokens):
        tokens = line_tokens(all_tokens)
        _, self.arguments = tokens.pop(0), tokens
        self.body = get_body(all_tokens, loc(_))


class ElseBlock(ELIFBlock):
    def is_true(self, macros):
        return True

    @property
    def arguments(self):
        return []

    @arguments.setter
    def arguments(self, values):
        if values:
            raise ValueError('{l} {block} got arguments {args} but expected None.'.format(
                l=loc(self), block=self.__class__.__name__, args=values
            ))


class IFDefBlock(IFBlock):
    def is_true(self, macros):
        return self.arguments and self.arguments[0] in macros


class IFNDefBlock(IFDefBlock):
    def is_true(self, macros):
        return not super(IFNDefBlock, self).is_true(macros)


def if_block(all_tokens, macros, new_tokens, line, current_token):
    return if_block.rules[current_token](all_tokens, macros, new_tokens, line, current_token)
if_block.rules = {
    TOKENS.PIF: IFBlock,
    TOKENS.PIFDEF: IFDefBlock,
    TOKENS.PIFNDEF: IFNDefBlock,
}