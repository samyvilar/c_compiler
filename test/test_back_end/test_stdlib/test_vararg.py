__author__ = 'samyvilar'

from test.test_back_end.test_stdlib.base import TestStdLib
from front_end.parser.ast.expressions import ConstantExpression, IntegerType

class TestVarArg(TestStdLib):
    def test_var_arg_function(self):
        code = """
        #include <stdarg.h>

        struct temp {int i; struct {int v[10]; char c;} s;};

        int foo(int initial, ...)
        {
            va_list values;
            va_start(values, initial);

            int a = va_arg(values, int);
            char c = va_arg(values, char);
            double d = va_arg(values, double);
            struct temp s = va_arg(values, struct temp);
            int last = va_arg(values, int);

             return a == -1 && c == 'c'&& d == 12.5 && s.i == 1 && s.s.c == 'f' && last == 10;
        }

        int main()
        {
            struct temp s = {1, .s = {.c = 'f'}};
            return foo(0, -1, 'c', 12.5, s, 10);
        }
        """
        self.evaluate(code)
        self.assert_base_element(ConstantExpression(1, IntegerType()))
        # self.assertEqual(self.mem[self.cpu.stack_pointer], 1)
