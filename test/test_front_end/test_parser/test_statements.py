__author__ = 'samyvilar'

from unittest import TestCase

from front_end.tokenizer.tokenize import Tokenize
from front_end.preprocessor.preprocess import Preprocess
from front_end.parser.declarations.declarations import translation_unit


class TestStatements(TestCase):
    def test_compound(self):
        source = """
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
        comp = translation_unit(Preprocess(Tokenize(source)))



