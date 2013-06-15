__author__ = 'samyvilar'

from unittest import TestCase
from front_end.tokenizer.tokenize import Tokenize
from front_end.preprocessor.preprocess import Preprocess


class TestPreProcessor(TestCase):
    def test_pre_processor(self):
        source = """

#define a 1
#define b(a) a

#if defined(b) - 1 + defined a
b(a)
#else
1
#endif
"""

        tokens = Preprocess(Tokenize(source))
        self.assertEqual(tokens, ['1'])

