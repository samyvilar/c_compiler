__author__ = 'samyvilar'

from itertools import imap, izip, repeat, count, chain

from utils.symbol_table import SymbolTable

from front_end.loader.locations import Location
from front_end.loader.load import Str
from utils.sequences import peek, consume, peek_or_terminal, terminal
from utils.errors import error_if_not_value, error_if_not_type, raise_error
from front_end.loader.locations import loc, EOFLocation, EOLLocation, LocationNotSet
from front_end.tokenizer.tokens import TOKENS, IDENTIFIER, INTEGER, KEYWORD, STRING, IGNORE
from front_end.tokenizer.tokens import copy_token, filter_out_empty_tokens

from front_end.tokenizer.tokenize import tokenize


class ObjectMacro(object):
    def __init__(self, name, _body=()):
        self.name, self._body = name, _body

    def body(self, location, arguments=(), macros=()):
        return iter(self._body)


class DefinedMacro(ObjectMacro):
    def __init__(self):
        super(DefinedMacro, self).__init__(TOKENS.DEFINED)

    def body(self, location, arguments=(), macros=()):
        if peek_or_terminal(arguments) == TOKENS.LEFT_PARENTHESIS and consume(arguments):
            name = error_if_not_type(consume(arguments, EOFLocation), (IDENTIFIER, KEYWORD))
            _ = error_if_not_value(arguments, TOKENS.RIGHT_PARENTHESIS)
        elif isinstance(peek_or_terminal(arguments), (IDENTIFIER, KEYWORD)):
            name = consume(arguments)
        else:
            raise ValueError(
                '{l} Expected either LEFT_PARENTHESIS or IDENTIFIER for function macro defined got {g}'.format(
                    l=location or EOLLocation, g=peek(arguments, ''))
            )
        yield INTEGER(str(int(name in macros)), loc(name))


def argument(
        token_seq,      # a non empty argument terminates with either a comma or right parenthesis ...
        takewhile=lambda token_seq: peek(token_seq, TOKENS.COMMA) not in {TOKENS.COMMA, TOKENS.RIGHT_PARENTHESIS}
):
    while takewhile(token_seq):
        if peek_or_terminal(token_seq) == TOKENS.LEFT_PARENTHESIS:  # nested parenthesis
            yield consume(token_seq)
            for token in argument(
                    token_seq,  # recursively call argument chaining all the nested parenthesis, until last right is hit
                    takewhile=lambda token_seq: peek(token_seq, TOKENS.RIGHT_PARENTHESIS) != TOKENS.RIGHT_PARENTHESIS
            ):
                yield token
            yield error_if_not_value(token_seq, TOKENS.RIGHT_PARENTHESIS)
        else:
            yield consume(token_seq)


def arguments(token_seq, parameters, l=LocationNotSet):
    parameters = iter(parameters)
    # empty (no) arguments ... but expects at least one parameter ... so use empty string ...
    if peek(token_seq, TOKENS.RIGHT_PARENTHESIS) == TOKENS.RIGHT_PARENTHESIS \
       and consume(parameters, terminal) is not terminal:
        yield IGNORE(location=(loc(peek(token_seq)) or l)),
    while peek(token_seq, TOKENS.RIGHT_PARENTHESIS) != TOKENS.RIGHT_PARENTHESIS:
        if isinstance(peek_or_terminal(parameters), FunctionMacroVariadicArgument):
            tokens = (IGNORE(location=loc(peek(token_seq))),) \
                if peek(token_seq) == TOKENS.RIGHT_PARENTHESIS else argument(
                    token_seq,  # if the current parameter is variadic argument get everything including commas ...
                    takewhile=lambda token_seq: peek(token_seq, TOKENS.RIGHT_PARENTHESIS) != TOKENS.RIGHT_PARENTHESIS
                )  # if at the end of arguments emit emtpy string ...
        elif peek_or_terminal(token_seq) == TOKENS.COMMA:  # if comma than argument is just an empty string ...
            tokens = IGNORE(location=loc(peek(token_seq))),
        else:
            tokens = argument(token_seq)
        _ = consume(parameters, None)
        yield tokens
        if peek_or_terminal(token_seq) != TOKENS.RIGHT_PARENTHESIS:  # if not at end we are expecting a comma ...
            location = loc(error_if_not_value(token_seq, TOKENS.COMMA, l))
            if peek_or_terminal(token_seq) == TOKENS.RIGHT_PARENTHESIS \
               and isinstance(peek_or_terminal(parameters), FunctionMacroArgument):
                _ = consume(parameters)  # if we read a comma and we are at end still expect at least one more parameter
                yield IGNORE(location=location),  # yield empty string ...
    if isinstance(consume(parameters, None), FunctionMacroVariadicArgument):
        yield IGNORE(location=(loc(peek(token_seq)) or l)),
    _ = error_if_not_value(token_seq, TOKENS.RIGHT_PARENTHESIS, location=l)


class FunctionMacroArgument(IDENTIFIER):
    pass


class FunctionMacroVariadicArgument(IDENTIFIER):
    pass


class FunctionMacro(ObjectMacro):
    def __init__(self, name, arguments, body):
        self.arguments = arguments
        super(FunctionMacro, self).__init__(name, body)

    def body(self, location, tokens=(), macros=None):
        macros = macros or Macros()
        location = loc(error_if_not_value(tokens, TOKENS.LEFT_PARENTHESIS)) or location
        all_args = tuple(
            (args, tuple(expand_all(iter(args), macros)))
            for args in imap(tuple, arguments(tokens, self.arguments, location))
        )

        _ = len(all_args) != len(self.arguments) and raise_error(
            '{l} Macro function {f} requires {t} arguments but got {g}.'.format(
                f=self.name, t=len(self.arguments), g=len(all_args), l=location))

        def _get_original_arguments(token, arguments):
            return arguments.get(token, ((token,),))[0]

        def _get_expanded_arguments(token, arguments):
            return arguments.get(token, (None, (token,)))[1]

        def _token_body(body_tokens, args):
            for token in imap(consume, repeat(body_tokens)):
                if peek_or_terminal(body_tokens) == TOKENS.PP:  # if tokens to be merged use original args unexpanded
                    for t in _get_original_arguments(token, args):
                        yield t
                    yield consume(body_tokens)
                    for t in _get_original_arguments(consume(body_tokens, IGNORE()), args):
                        yield t
                elif token != TOKENS.PP and token.startswith(TOKENS.NUMBER_SIGN):
                    yield STRING(' '.join(imap(str, args.get(token[1:], ((token[1:],),))[0])),  loc(token))
                else:
                    for t in _get_expanded_arguments(token, args):  # get expansion if present otherwise token ...
                        yield t

        def _merge_tokens(tokens):
            for token in imap(consume, repeat(tokens)):
                if token == TOKENS.PP:
                    token = IGNORE()
                while peek_or_terminal(tokens) == TOKENS.PP and consume(tokens):
                    new_token_source = token + consume(tokens, IGNORE())
                    new_tokens = tokenize(imap(Str, new_token_source, imap(
                        Location,
                        repeat(loc(token).file_name, len(new_token_source)),
                        repeat(loc(token).line_number),
                        count(loc(token).column_number),
                    )))
                    token = next(new_tokens, IGNORE())
                    terminal_token = next(new_tokens, terminal)
                    if terminal_token is not terminal:
                        raise ValueError(
                            '{l} token pasting generated more than one token {t} {e}'.format(
                                l=loc(token), t=token, e=terminal_token
                            ))
                if token == TOKENS.PP:
                    token = IGNORE()
                yield token

        return filter_out_empty_tokens(  # filter out all the empty/whitespace tokens
            _merge_tokens(_token_body(iter(self._body), dict(izip(self.arguments, all_args))))
        )


def expand_all(tokens, macros, expanded_macros=None):
    return chain.from_iterable(
        imap(expand, imap(consume, repeat(tokens)), repeat(tokens), repeat(macros), repeat(expanded_macros))
    )


def expand(token, tokens, macros, expanded_macros=None):
    expanded_macros = expanded_macros or {}
    if token in macros and token not in expanded_macros:
        if peek_or_terminal(tokens) != TOKENS.LEFT_PARENTHESIS and isinstance(macros[token], FunctionMacro):
            yield token  # don't expand function macros that aren't followed by a parenthesis ...
        else:
            token_body = macros[token].body(loc(token), tokens, macros=macros)  # get body ...
            expanded_macros[token] = token  # mark token so it doesn't get re expanded ...
            for t in expand_all(imap(consume, repeat(token_body)), macros, expanded_macros):  # expand body ...
                if peek_or_terminal(token_body) is terminal:  # if this is the last token check for further expansion
                    for _t in expand(t, tokens, macros, expanded_macros):
                        yield _t
                else:
                    yield t
            _ = expanded_macros.pop(token)  # expansion complete mark token so it can be re-expanded ...
    else:
        yield token


def reposition_tokens(tokens, new_location):
    tokens = iter(tokens)
    file_name, line_number, column_number = new_location.file_name, new_location.line_number, new_location.column_number
    for token in imap(consume, repeat(tokens)):
        new_token = copy_token(token, Location(file_name, line_number, column_number))  # create a new token with new l
        yield new_token
        # update column for next token to take into account the previous location
        # if the two tokens where originally next to each other
        previous_location = loc(token)  # get original location
        next_location = loc(peek(tokens, EOFLocation))

        if previous_location.column_number + len(token) == next_location.column_number:
            column_number += len(token)  # keep adjacent tokens together
        else:
            column_number += len(token) + 1  # emit single space for anything greater than space ...


class Macros(SymbolTable):
    def __init__(self, args=(), **kwargs):
        super(Macros, self).__init__(chain(args, ((TOKENS.DEFINED, DefinedMacro()),), kwargs.iteritems()))

    def __contains__(self, item, search_all=True):
        return super(Macros, self).__contains__(item, search_all)

    def get(self, k, default=None, all_tokens=iter(())):
        if k in self:
            for token in reposition_tokens(expand(k, all_tokens, self), loc(k)):  # imap(copy_token, expand(k, all_tokens, self), repeat(loc(k))):
                yield token
        else:
            yield default