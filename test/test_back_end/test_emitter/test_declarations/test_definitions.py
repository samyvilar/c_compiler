__author__ = 'samyvilar'

from unittest import TestCase
from collections import defaultdict

from front_end.loader.load import source
from front_end.tokenizer.tokenize import tokenize
from front_end.preprocessor.preprocess import preprocess

from front_end.parser.parse import parse
from front_end.parser.symbol_table import SymbolTable

from back_end.emitter.emit import emit
from back_end.emitter.types import size
from back_end.emitter.cpu import evaluate, load, CPU, executable, push, pop, push_frame, pop_frame, Halt
from back_end.emitter.cpu import address


class TestDeclarations(TestCase):
    def evaluate(self, code):
        address_gen, symbol_table, self.cpu, self.mem = address(), SymbolTable(), CPU(), defaultdict(int)
        load(
            executable(emit(parse(preprocess(tokenize(source(code))))), symbol_table),
            self.mem,
            symbol_table,
            address_gen
        )

        push(0, self.cpu, self.mem)
        push_frame(None, self.cpu, self.mem)
        push(next(address_gen) - size(Halt('')), self.cpu, self.mem)
        self.cpu.instr_pointer = symbol_table['main'].address
        evaluate(self.cpu, self.mem)
        pop_frame(None, self.cpu, self.mem)
        pop(self.cpu, self.mem)


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