__author__ = 'samyvilar'

from unittest import TestCase
from front_end.loader.load import source
from front_end.tokenizer.tokenize import tokenize
from front_end.preprocessor.preprocess import preprocess
from front_end.parser.declarations.declarations import declaration


class TestErrors(TestCase):
    def test_missing_semicolon(self):
        code = "int a"
        self.assertRaises(ValueError, list, declaration(preprocess(tokenize(source(code))), {}))

    def test_extra_values(self):
        code = """
        #define foo
        #undef foo error!
        """
        self.assertRaises(ValueError, list, preprocess(tokenize(source(code))))

    def test_failed_expectation(self):
        code = "int a!"
        self.assertRaises(ValueError, list, declaration(preprocess(tokenize(source(code))), {}))