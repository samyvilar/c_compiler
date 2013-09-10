__author__ = 'samyvilar'

from test.test_back_end.test_emitter.test_declarations.test_definitions import TestDeclarations
from test.test_back_end.test_emitter.test_statements.test_compound import TestStatements


class TestPostfix(TestStatements):
    def test_increment(self):
        source = """
        {
            int a = 10;
            int b = a++;
        }
        """
        self.evaluate(source)
        self.assertEqual(self.mem[self.cpu.stack_pointer], 11)
        self.assertEqual(self.mem[self.cpu.stack_pointer - 1], 10)

    def test_decrement(self):
        source = """
        {
            int a = 10;
            int b = a--;
        }
        """
        self.evaluate(source)
        self.assertEqual(self.mem[self.cpu.stack_pointer], 9)
        self.assertEqual(self.mem[self.cpu.stack_pointer - 1], 10)

    def test_array_subscript(self):
        source = """
        {
            int b;
            int a[10];
            int c = 1;
            a[2] = 10;
            b = a[2];
            a[0] = -1;
            a[9] = -1;

        }
        """
        self.evaluate(source)
        self.assertEqual(self.mem[self.cpu.stack_pointer], 10)
        self.assertEqual(self.mem[self.cpu.stack_pointer - 11], 1)

    def test_two_d_array(self):
        source = """
        {
            int b;
            int a[5][3];
            a[2][2] = 5;
            b = a[2][2];
        }
        """
        self.evaluate(source)
        self.assertEqual(self.mem[self.cpu.stack_pointer], 5)

    def test_struct_member_selection(self):
        source = """
        {
            double value;
            struct foo {
                int a;
                double b;
                char e;
            } a, b;
            int offset = -1;
            a.b = 4;
            value = a.b;
        }
        """
        self.evaluate(source)
        self.assertEqual(self.mem[self.cpu.stack_pointer], 4)

    def test_nested_struct_member_selection(self):
        source = """
        {
            int value;
            struct foo {
                int a;
                struct foo2 {
                    double b;
                    char g[10];
                } n;
                char e;
            } a, b;
            double c, d;
            a.n.g[2] = 'a';
            value = a.n.g[2];
        }
        """
        self.evaluate(source)
        self.assertEqual(self.mem[self.cpu.stack_pointer], ord('a'))

    def test_struct_member_selection_pointer(self):
        source = """
        {
            int value;
            struct foo {
                int a;
                struct foo2 {
                    char a;
                    int g[10];
                    double c;
                } *b, c;
                char d;
            } a, *b;
            int d;

            a.b = &a.c;
            b = &a;
            b->b->g[2] = 10;
            value = b->b->g[2];
        }
        """
        self.evaluate(source)
        self.assertEqual(self.mem[self.cpu.stack_pointer], 10)

    # def test_compound_literal(self):
    #     code = """
    #     {
    #         int value;
    #         value = (int){1} + 1;
    #     }
    #     """
    #     super(TestPostfix, self).evaluate(code)
    #     self.assertEqual(self.mem[self.cpu.stack_pointer], 1)


class TestPostFixFunction(TestDeclarations):
    def test_function_call(self):
        source = """
        int a;
        void foo()
        {  a = 10; }
        int main()
        {
            foo();
            return a;
        }
        """
        self.evaluate(source)
        self.assertEqual(self.mem[self.cpu.stack_pointer], 10)

    def test_function_call_parameters(self):
        source = """
        int a;
        void foo(int a1){ a = a1; }
        int main()
        {
            foo(10);
            return a;
        }
        """
        self.evaluate(source)
        self.assertEqual(self.mem[self.cpu.stack_pointer], 10)

    def test_function_return(self):
        source = """
        int a;
        int foo1(int a1) {  return a1; }
        double foo(int a2, double a3) {  return a2; }
        double main()
        {
            return foo(foo1(11), 10);
        }
        """
        self.evaluate(source)
        self.assertEqual(self.mem[self.cpu.stack_pointer], 11.0)

    def test_function_struct_return(self):
        source = """
        int a;
        struct foo {int a; char b[10]; double v;};
        struct foo test(char f)
        {
            struct foo c;
            c.b[2] = f;
            return c;
        }

        int main()
        {
            struct foo v = test('a');
            return v.b[2];
        }
        """
        self.evaluate(source)
        self.assertEqual(self.mem[self.cpu.stack_pointer], ord('a'))

    def test_function_pointer(self):
        source = """
        int foo(int value){ return value + 1; }
        int main()
        {
            int (*foo_fp)(int) = &foo;
            return foo_fp(10);
        }
        """
        self.evaluate(source)
        self.assertEqual(self.mem[self.cpu.stack_pointer], 11)