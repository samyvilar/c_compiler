__author__ = 'samyvilar'

from unittest import TestCase
from collections import defaultdict

from front_end.loader.load import source
from front_end.tokenizer.tokenize import tokenize
from front_end.preprocessor.preprocess import preprocess

from front_end.parser.parse import parse
from front_end.parser.symbol_table import SymbolTable

from back_end.emitter.emit import emit
from back_end.linker.link import executable
from back_end.emitter.cpu import CPU, load, address, evaluate


class TestDeclarations(TestCase):
    def evaluate(self, code):
        address_gen, symbol_table, self.cpu, self.mem = address(), SymbolTable(), CPU(), defaultdict(int)
        load(
            executable(emit(parse(preprocess(tokenize(source(code))))), symbol_table),
            self.mem,
            symbol_table,
            address_gen
        )
        evaluate(self.cpu, self.mem)


class TestDefinitions(TestDeclarations):
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
        super(TestDefinitions, self).evaluate(source)