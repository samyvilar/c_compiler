__author__ = 'samyvilar'

from unittest import TestCase

from front_end.tokenizer.tokenize import Tokenize
from front_end.preprocessor.preprocess import Preprocess
from front_end.parser.declarations.declarations import translation_unit

from back_end.emitter.emit import Emit


class TestDefinitions(TestCase):
    def test_definition(self):
        source = """
        int a = 1;
        double b[100];

        void foo(){}

        int main()
        {
            b[2] = 4;
            return 0;
        }
        """
        ext_decs = Emit(translation_unit(Preprocess(Tokenize(source))))