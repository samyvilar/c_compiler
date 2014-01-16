__author__ = 'samyvilar'

from unittest import TestCase

from front_end.loader.load import source
from front_end.tokenizer.tokenize import tokenize
from front_end.preprocessor.preprocess import preprocess

from front_end.parser.parse import parse
from front_end.parser.symbol_table import SymbolTable

from back_end.emitter.emit import emit
from back_end.linker.link import executable, set_addresses, resolve
from back_end.emitter.cpu import CPU, VirtualMemory, evaluate, base_element
from back_end.emitter.c_types import size, exp

from front_end.parser.ast.expressions import ConstantExpression, IntegerType

from back_end.loader.load import load


class TestDeclarations(TestCase):
    def evaluate(self, code):
        symbol_table, self.cpu, self.mem = SymbolTable(), CPU(), VirtualMemory()

        load(
            set_addresses(
                resolve(executable(emit(parse(preprocess(tokenize(source(code))))), symbol_table), symbol_table)
            ),
            self.mem,
        )

        evaluate(self.cpu, self.mem)

    def assert_base_element(self, element):
        self.assertEqual(base_element(self.cpu, self.mem, size(element)), exp(element))


class TestDefinitions(TestDeclarations):
    def test_definition(self):
        code = """
        int a = 1;
        double b[100];

        void foo(){}

        int main()
        {
            b[2] = 4;
            return b[2];
        }
        """
        self.evaluate(code)
        self.assert_base_element(ConstantExpression(4, IntegerType()))

    def test_static_definitions(self):
        code = """

        int foo(int call_number)
        {
            static int d = 10;
            static char cs[6] = "hello";

            if (call_number == 1)
            {
                if (d != 10 || cs[4] != 'o')
                    return -1;
                d = 1;
                cs[4] = 'l';
            }

            if (call_number == 2)
            {
                if (d != 1 || cs[4] != 'l')
                    return -1;
                d = 2;
                cs[0] = 'g';
            }

            if (call_number == 3)
            {
                if (d != 2 || cs[0] != 'g')
                    return -1;
            }

            return 0;
        }

        int main()
        {
            foo(0);
            int call_1 = foo(1);
            foo(0);
            int call_2 = foo(2);
            int call_3 = foo(3);
            return !(call_1 || call_2 || call_3);
        }
        """
        self.evaluate(code)
        self.assert_base_element(ConstantExpression(1, IntegerType()))


class TestInitializer(TestDeclarations):
    def test_global_constant_initializer(self):
        code = """
        struct {int a; char b; int c[10]; struct {int a; double c;} foo[10];}
            foo = {.a=10, .c[1] = -1, .foo[0 ... 2] = {-1, -1} };

        int main()
        {
            return foo.a == 10 && foo.c[1] == -1 && foo.foo[0].a == -1 && foo.foo[1].c == -1 && foo.foo[3].c == 0;
        }
        """
        self.evaluate(code)
        self.assert_base_element(ConstantExpression(1, IntegerType()))
        # self.assertEqual(1, self.mem[self.cpu.stack_pointer])

    def test_local_initializer(self):
        code = """
        int main()
        {
            struct {int a; char b; int c[10]; struct {int a; double c;} foo[10];}
                foo = {.a=10, .c[1] = -1, .foo[0 ... 2] = {-1, -1} };

            return foo.a == 10 && foo.c[1] == -1 && foo.foo[0].a == -1 && foo.foo[1].c == -1.0 && foo.foo[3].c == 0.0;
        }
        """
        self.evaluate(code)
        self.assert_base_element(ConstantExpression(1, IntegerType()))
        # self.assertEqual(1, self.mem[self.cpu.stack_pointer])

    def test_global_union_initializer(self):
        code = """
            union {unsigned long long a; double b; char c[20]; int d[0];} foo = {.a=10, .b=10.5};

            int main()
            {
                return foo.b == 10.5;
            }
            """
        self.evaluate(code)
        self.assert_base_element(ConstantExpression(1, IntegerType()))
        # self.assertEqual(1, self.mem[self.cpu.stack_pointer])