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

        self.cpu.instr_pointer = min(self.mem.iterkeys())
        evaluate(self.cpu, self.mem)


class TestDefinitions(TestDeclarations):
    def test_definition(self):
        code = """
        int a = 1;
        double b[100];

        void foo(){}

        int main()
        {
            b[2] = 4;
            return 0;
        }
        """
        super(TestDefinitions, self).evaluate(code)


class TestInitializer(TestDeclarations):
    def test_global_constant_initializer(self):
        code = """
        struct {int a; char b; int c[10]; struct {int a; double c;} foo[10];}
            foo = {.a=10, .c[1] = -1, .foo[0 ... 2] = {-1, -1} };

        int main()
        {
            return foo.a == 10 && foo.c[1] == -1 && foo.foo[0].a == -1 && foo.foo[1].c == -1 && foo.foo[3].c == 0.0;
        }
        """
        super(TestInitializer, self).evaluate(code)
        self.assertEqual(1, self.mem[self.cpu.stack_pointer])

    def test_local_initializer(self):
        code = """
        int main()
        {
            struct {int a; char b; int c[10]; struct {int a; double c;} foo[10];}
                foo = {.a=10, .c[1] = -1, .foo[0 ... 2] = {-1, -1} };

            return foo.a == 10 && foo.c[1] == -1 && foo.foo[0].a == -1 && foo.foo[1].c == -1 && foo.foo[3].c == 0.0;
        }
        """
        super(TestInitializer, self).evaluate(code)
        self.assertEqual(1, self.mem[self.cpu.stack_pointer])