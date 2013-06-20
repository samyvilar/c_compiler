__author__ = 'samyvilar'

from collections import defaultdict
from unittest import TestCase
from front_end.tokenizer.tokenize import Tokenize
from front_end.preprocessor.preprocess import Preprocess

import front_end.parser.statements.compound as parser
import back_end.emitter.statements.statement as emitter

from back_end.emitter.cpu import load, evaluate, CPU


class TestStatements(TestCase):
    def evaluate(self, source):
        self.cpu, self.mem = CPU(), defaultdict(int)
        load(emitter.statement(parser.statement(Preprocess(Tokenize(source)))), self.mem, {})
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



