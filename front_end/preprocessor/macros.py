__author__ = 'samyvilar'

from sequences import peek, consume
from front_end.errors import error_if_not_value, error_if_not_type
from front_end.loader.locations import loc
from front_end.tokenizer.tokens import TOKENS, IDENTIFIER, INTEGER


class ObjectMacro(object):
    def __init__(self, name, _body):
        self.name, self._body = name, _body

    def body(self, tokens=()):
        return self._body


class FunctionMacro(ObjectMacro):
    def __init__(self, name, arguments, body):
        self.arguments = arguments
        super(FunctionMacro, self).__init__(name, body)

    def body(self, tokens=()):
        if peek(tokens, default='') != TOKENS.LEFT_PARENTHESIS:
            return [self.name]

        location = loc(error_if_not_value(tokens, TOKENS.LEFT_PARENTHESIS))
        args, nested_level = [], 0
        while peek(tokens, default='') != TOKENS.RIGHT_PARENTHESIS:
            args.append([])
            while peek(tokens, default='') not in {TOKENS.COMMA, TOKENS.RIGHT_PARENTHESIS}:
                if peek(tokens, default='') == TOKENS.LEFT_PARENTHESIS:
                    while peek(tokens, default='') != TOKENS.RIGHT_PARENTHESIS and not nested_level:
                        if peek(tokens) == TOKENS.LEFT_PARENTHESIS:
                            nested_level += 1
                        if peek(tokens) == TOKENS.RIGHT_PARENTHESIS:
                            nested_level -= 1
                        args[-1].append(consume(tokens))
                    args[-1].append(error_if_not_value(tokens, TOKENS.RIGHT_PARENTHESIS))
                else:
                    args[-1].append(consume(tokens))
            _ = peek(tokens, default='') == TOKENS.COMMA and consume(tokens)
        _ = error_if_not_value(tokens, TOKENS.RIGHT_PARENTHESIS)

        if len(args) != len(self.arguments):
            raise ValueError('{l} Macro function {f} requires {t} arguments but got {g}.'.format(
                f=self.name, t=len(self.arguments), g=len(args), l=location
            ))

        expansion, new_tokens = {arg: args[index] for index, arg in enumerate(self.arguments)}, []
        for token in self._body:
            new_tokens.extend(expansion.get(token, [token]))
        return new_tokens


class DefinedMacro(FunctionMacro):
    def __init__(self, macros):
        self.macros = macros
        super(DefinedMacro, self).__init__(TOKENS.DEFINED, ['argument'], [])

    def body(self, arguments=()):
        if peek(arguments, default='') == TOKENS.LEFT_PARENTHESIS:
            _ = error_if_not_value(arguments, TOKENS.LEFT_PARENTHESIS)
            name = error_if_not_type(arguments, IDENTIFIER)
            _ = error_if_not_value(arguments, TOKENS.RIGHT_PARENTHESIS)
        elif isinstance(peek(arguments, default=''), IDENTIFIER):
            name = error_if_not_type(arguments, IDENTIFIER)
        else:
            raise ValueError('Expected either LEFT_PARENTHESIS or IDENTIFIER for function macro defined')
        return [INTEGER('1', loc(name)) if name in self.macros else INTEGER('0', loc(name))]


class Macros(dict):
    def __init__(self):
        super(Macros, self).__init__()
        self[TOKENS.DEFINED] = DefinedMacro(self)

    def get(self, k, d=None, all_tokens=()):
        location = loc(k)
        if k in self:
            expand_tokens, expanded_tokens, new_tokens = [k], {}, []
            while expand_tokens:
                token = expand_tokens.pop(0)
                if token in self and token not in expanded_tokens:
                    expand_tokens.extend(self[token].body(all_tokens))
                else:
                    new_tokens.append(token)
                expanded_tokens[token] = token
            for token in new_tokens:
                yield token.__class__(token, location)
        elif d is not None:
            yield d
        else:
            yield super(Macros, self).__getitem__(k)
