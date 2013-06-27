__author__ = 'samyvilar'


from front_end.tokenizer.tokenize import Tokenize
from front_end.preprocessor.directives import get_directives
from front_end.preprocessor.macros import Macros


class Preprocess(Tokenize):
    def __init__(self, tokens, directives=None):
        new_tokens, macros = [], Macros()
        directives = directives or get_directives()

        while tokens:
            tokens = directives[tokens[0]](tokens, macros, new_tokens)

        super(Preprocess, self).__init__(new_tokens)