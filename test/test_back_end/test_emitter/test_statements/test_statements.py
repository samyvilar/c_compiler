__author__ = 'samyvilar'

from collections import defaultdict
from unittest import TestCase
from front_end.loader.load import source
from front_end.tokenizer.tokenize import tokenize
from front_end.preprocessor.preprocess import preprocess

import front_end.parser.statements.compound as parser
import back_end.emitter.statements.statement as emitter

from back_end.emitter.cpu import load, evaluate, CPU


class TestStatements(TestCase):
    def evaluate(self, code):
        self.cpu, self.mem = CPU(), defaultdict(int)
        load(emitter.statement(next(parser.statement(preprocess(tokenize(source(code)))))), self.mem, {})
        evaluate(self.cpu, self.mem)


class TestCompoundStatement(TestStatements):
    def test_compound_statement(self):
        source = """
        {
            int a = 10;
            {
                int a1 = 1;
            }
            a = a;
        }
        """
        super(TestCompoundStatement, self).evaluate(source)
        self.assertEqual(self.mem[self.cpu.stack_pointer], 10)



