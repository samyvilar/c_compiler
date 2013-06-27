__author__ = 'samyvilar'

from unittest import TestCase
from front_end.tokenizer.tokenize import Tokenize
from front_end.preprocessor.preprocess import Preprocess
from front_end.parser.declarations.declarations import declaration


class TestErrors(TestCase):
    def test_missing_semicolon(self):
        source = "int a"
        self.assertRaises(ValueError, declaration, Preprocess(Tokenize(source)), {})

    def test_extra_values(self):
        source = """
        #define foo
        #undef foo error!
        """
        self.assertRaises(ValueError, Preprocess, Tokenize(source), {})

    def test_failed_expectation(self):
        source = "int a!"
        self.assertRaises(ValueError, declaration, Preprocess(Tokenize(source)), {})