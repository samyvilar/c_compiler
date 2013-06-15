__author__ = 'samyvilar'

from front_end.tokenizer import logger
from front_end import List, consumed
from front_end.loader.locations import loc, Str
from front_end.loader.load import Load
from front_end.tokenizer.parser import get_parsing_functions
from front_end.tokenizer.tokens import IGNORE, TOKEN


def line_tokens(tokens):  # get all the tokens on the current line, being that preprocessor work on a line-by-line basis
    if not tokens:
        return tokens
    tokens_on_current_line = Tokenize([tokens.pop(0)])
    while tokens and loc(tokens[0]).line_number == loc(tokens_on_current_line[0]).line_number:
        tokens_on_current_line.append(tokens.pop(0))
    return tokens_on_current_line


class Tokenize(List):
    def __init__(self, values=(), parsing_functions=get_parsing_functions()):
        tokens = []
        if values and isinstance(values[0], TOKEN):  # if values is already Token Array do nothing.
            tokens = values
        elif values:
            if not isinstance(values[0], Str):  # if source is string set locations.
                values = Load(file_like='__SOURCE__', source=values)
            while values:
                token = parsing_functions[values[0]](values)
                if not isinstance(token, IGNORE):
                    tokens.append(token)
            logger.debug(
                'Created {t} tokens from {c} chars'.format(t=len(tokens), c=len(consumed(values))),
                extra={'location': loc(tokens[0]).file_name},
            )
        super(Tokenize, self).__init__(tokens)
