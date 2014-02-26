__author__ = 'samyvilar'

from unittest import TestCase

from front_end.loader.load import source
from front_end.tokenizer.tokenize import tokenize
from front_end.preprocessor.preprocess import preprocess
from front_end.parser import translation_unit

from front_end.parser.ast.statements import FunctionDefinition


class TestStatements(TestCase):
    def test_compound(self):
        code = """
            int main()
            {
                int a = 1 + 2;
                label:
                for (a = 0; a < 3; a++)
                    a;
                goto label;
                return 0;
            }
        """
        got_values = translation_unit(preprocess(tokenize(source(code))))
        self.assert_(isinstance(next(got_values), FunctionDefinition))





