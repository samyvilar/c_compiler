__author__ = 'samyvilar'

from itertools import izip_longest, chain, imap

from front_end.loader.load import Str
from sequences import peek, consume, takewhile
from front_end.errors import error_if_not_value, error_if_not_type
from front_end.loader.locations import loc, EOFLocation
from front_end.tokenizer.tokens import TOKENS, IDENTIFIER, INTEGER, KEYWORD, STRING, IGNORE

from front_end.tokenizer.tokenize import tokenize


class ObjectMacro(object):
    def __init__(self, name, _body):
        self.name, self._body = name, _body

    def body(self, tokens=()):
        return (token.__class__(token, loc(token)) for token in self._body)


def argument(
        token_seq,
        takewhile=lambda token_seq:
        peek(token_seq, TOKENS.COMMA) not in {TOKENS.COMMA, TOKENS.RIGHT_PARENTHESIS}
):
    while takewhile(token_seq):
        if peek(token_seq, '') == TOKENS.LEFT_PARENTHESIS:
            yield consume(token_seq)
            for t in argument(token_seq,
                              takewhile=lambda token_seq:
                              peek(token_seq, TOKENS.RIGHT_PARENTHESIS) != TOKENS.RIGHT_PARENTHESIS):
                yield t
            yield error_if_not_value(token_seq, TOKENS.RIGHT_PARENTHESIS)
        else:
            yield consume(token_seq)


def arguments(token_seq):
    while peek(token_seq, TOKENS.RIGHT_PARENTHESIS) != TOKENS.RIGHT_PARENTHESIS:
        yield argument(token_seq)
        if peek(token_seq, '') == TOKENS.COMMA:
            _ = consume(token_seq)
        elif peek(token_seq, '') != TOKENS.RIGHT_PARENTHESIS:
            raise ValueError('{l} expected either COMMA or RIGHT_PARENTHESIS got {g}'.format(
                l=loc(peek(token_seq, EOFLocation)), g=peek(token_seq, '')
            ))
    _ = error_if_not_value(token_seq, TOKENS.RIGHT_PARENTHESIS)


class FunctionMacro(ObjectMacro):
    def __init__(self, name, arguments, body):
        self.arguments = arguments
        super(FunctionMacro, self).__init__(name, body)

    def body(self, tokens=()):
        if peek(tokens, '') != TOKENS.LEFT_PARENTHESIS:
            return self.name, consume(tokens, default=IGNORE('', EOFLocation))

        location = loc(error_if_not_value(tokens, TOKENS.LEFT_PARENTHESIS))
        expansion = {arg: tuple(b) for b, arg in izip_longest(arguments(tokens) or (), self.arguments)}
        if len(expansion) != len(self.arguments):
            raise ValueError('{l} Macro function {f} requires {t} arguments but got {g}.'.format(
                f=self.name, t=len(self.arguments), g=len(expansion), l=location
            ))
        # Generate a new token objs sequence since, expand uses the token id to track expansions ...
        return imap(
            lambda token: token.__class__(token, loc(token)),
            chain.from_iterable(
                (STRING(' '.join(expansion.get(token[1:], (token,)))),)
                if token.startswith(TOKENS.NUMBER_SIGN) and token != TOKENS.PP else expansion.get(token, (token,))
                for token in self._body
            )
        )


def expand(token, tokens, macros, expanded_macros=None):
    _iter = lambda seq: takewhile(lambda _: True, iter(seq))
    expanded_macros = expanded_macros or {}

    if token in macros and id(token) not in expanded_macros:
        body = _iter(macros[token].body(tokens))
        expanded_macros[id(token)] = token
        return chain.from_iterable(expand(t, chain(body, _iter(tokens)), macros, expanded_macros) for t in body)
    else:
        return token,


def merge_tokens(token_seq):
    terminal = object()
    while peek(token_seq, terminal) is not terminal:
        prev_token = consume(token_seq)
        while peek(token_seq, '') == TOKENS.PP:
            _ = consume(token_seq)
            prev_token = next(tokenize((Str(c, loc(_)) for c in prev_token + consume(token_seq, IGNORE('')))))
        yield prev_token
    else:
        yield IGNORE('')


class DefinedMacro(FunctionMacro):
    def __init__(self, macros):
        self.macros = macros
        super(DefinedMacro, self).__init__(TOKENS.DEFINED, ('argument',), ())

    def body(self, arguments=()):
        if peek(arguments, '') == TOKENS.LEFT_PARENTHESIS:
            _ = consume(arguments)
            name = error_if_not_type(consume(arguments, EOFLocation), (IDENTIFIER, KEYWORD))
            _ = error_if_not_value(arguments, TOKENS.RIGHT_PARENTHESIS)
        elif isinstance(peek(arguments, ''), (IDENTIFIER, KEYWORD)):
            name = consume(arguments)
        else:
            raise ValueError('Expected either LEFT_PARENTHESIS or IDENTIFIER for function macro defined')
        return INTEGER('1', loc(name)) if name in self.macros else INTEGER('0', loc(name)),


class Macros(dict):
    def __init__(self):
        super(Macros, self).__init__()
        self[TOKENS.DEFINED] = DefinedMacro(self)

    def get(self, k, d=None, all_tokens=()):
        location = loc(k)
        if k in self:
            for token in merge_tokens(expand(k, all_tokens, self)):
                yield token.__class__(token, location)
        elif d is not None:
            yield d
        else:
            yield super(Macros, self).__getitem__(k)