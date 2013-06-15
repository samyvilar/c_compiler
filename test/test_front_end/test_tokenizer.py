__author__ = 'samyvilar'

from unittest import TestCase
from front_end.tokenizer.tokenize import Tokenize
from front_end.tokenizer.tokens import IDENTIFIER, KEYWORD, SYMBOL, PRE_PROCESSING_SYMBOL, INTEGER, FLOAT, STRING, CHAR


class TestTokenize(TestCase):
    def test_tokenize(self):
        source = """
#include "stdio.h"

int main()
{
    float a = .0;// this is a comment.
    char b = 'a';/* this is
    a multi-line comment */
    return 0;
}
"""
        new_tokens = Tokenize(source)
        tokens = (PRE_PROCESSING_SYMBOL('#include'), STRING('stdio.h'), KEYWORD('int'), IDENTIFIER('main'),
                  SYMBOL('('), SYMBOL(')'), SYMBOL('{'), KEYWORD('float'), IDENTIFIER('a'), SYMBOL('='),
                  FLOAT('.0'), SYMBOL(';'), KEYWORD('char'), IDENTIFIER('b'), SYMBOL('='), CHAR('a'),
                  SYMBOL(';'), KEYWORD('return'), INTEGER('0'), SYMBOL(';'), SYMBOL('}'))

        for index, token in enumerate(tokens):
            self.assertEqual(token, new_tokens[index])
            self.assertEqual(type(token), type(new_tokens[index]))
