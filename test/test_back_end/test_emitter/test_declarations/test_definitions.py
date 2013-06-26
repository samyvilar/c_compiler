__author__ = 'samyvilar'

from unittest import TestCase
from collections import defaultdict

from back_end.emitter.types import flatten
from front_end.tokenizer.tokenize import Tokenize
from front_end.preprocessor.preprocess import Preprocess
from front_end.parser.parse import Parse
from front_end.parser.symbol_table import SymbolTable

from back_end.emitter.emit import Emit
from back_end.emitter.cpu import evaluate, load, CPU, executable, push, pop, push_frame, pop_frame, Halt, Instruction


class TestDeclarations(TestCase):
    def evaluate(self, source):
        self.cpu, self.mem = CPU(), defaultdict(int)
        symbol_table = SymbolTable()

        bins = executable(Emit(Parse(Preprocess(Tokenize(source)))), symbol_table)
        load(bins, self.mem, symbol_table)

        push(0, self.cpu, self.mem)
        push_frame(None, self.cpu, self.mem)
        halt_addr = max(self.mem.iterkeys())
        assert isinstance(self.mem[halt_addr], Halt)
        push(halt_addr, self.cpu, self.mem)
        self.cpu.instr_pointer = next(flatten(symbol_table['main'].binaries, Instruction)).address
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