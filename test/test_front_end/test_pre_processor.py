__author__ = 'samyvilar'

from unittest import TestCase
from front_end.loader.load import source
from front_end.tokenizer.tokenize import tokenize
from front_end.preprocessor.preprocess import preprocess


class TestPreProcessor(TestCase):
    def test_pre_processor(self):
        code = """
            #define a 1
            #define b(a) a

            #if defined(b) - 1 + defined a
            b(a)
            #else
            1
            #endif
        """
        for token in preprocess(tokenize(source(code))):
            self.assertEqual(token, '1')

