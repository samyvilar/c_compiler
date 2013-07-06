__author__ = 'samyvilar'

from unittest import TestCase
from itertools import izip

from front_end.loader.load import source
from front_end.tokenizer.tokenize import tokenize
from front_end.tokenizer.tokens import IDENTIFIER, KEYWORD, SYMBOL, PRE_PROCESSING_SYMBOL, INTEGER, FLOAT, STRING, CHAR


class TestTokenize(TestCase):
    def test_tokenize(self):
        code = """
#include "stdio.h"

int main()
{
    float a = .0;// this is a comment.
    char b = 'a';/* this is
    a multi-line comment */
    int a = 1 / 2;
    return 0;
}
"""
        new_tokens = tokenize(source(code))
        tokens = (PRE_PROCESSING_SYMBOL('#include'), STRING('stdio.h'), KEYWORD('int'), IDENTIFIER('main'),
                  SYMBOL('('), SYMBOL(')'), SYMBOL('{'), KEYWORD('float'), IDENTIFIER('a'), SYMBOL('='),
                  FLOAT('.0'), SYMBOL(';'), KEYWORD('char'), IDENTIFIER('b'), SYMBOL('='), CHAR('a'),
                  SYMBOL(';'), KEYWORD('int'), IDENTIFIER('a'), SYMBOL('='), INTEGER(1), SYMBOL('/'), INTEGER(2),
                  SYMBOL(';'), KEYWORD('return'), INTEGER('0'), SYMBOL(';'), SYMBOL('}'))

        for exp_token, got_token in izip(tokens, new_tokens):
            self.assertEqual(exp_token, got_token)
            self.assertEqual(type(exp_token), type(got_token))
