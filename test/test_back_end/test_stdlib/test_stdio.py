__author__ = 'samyvilar'

import sys

from test.test_back_end.test_stdlib.base import TestStdLib
from back_end.emitter.cpu import Kernel
from back_end.emitter.system_calls import CALLS
from StringIO import StringIO


class TestPrintf(TestStdLib):
    def evaluate(self, code, cpu=None, mem=None, os=None):
        self.os = Kernel(CALLS)
        self.os.opened_files = {io_id: StringIO() for io_id in self.os.opened_files}
        super(TestPrintf, self).evaluate(code, cpu, mem, os=self.os)
        self.stdout = self.os.opened_files[getattr(sys.stdout, 'fileno', lambda: 1)()]
        self.stdout.seek(0)

    def test_printf_string(self):
        code = """
        #include <stdio.h>

        int main()
        {
            char temp[100] = "Hello";
            char *temp_1 = "World";
            printf("%s", temp);
            printf("%s%s", temp_1, "!");

            return 0;
        }
        """
        self.evaluate(code)
        self.assertEqual(self.stdout.read(), 'HelloWorld!')

    def test_printf_int(self):
        code = """
        #include <stdio.h>

        int main()
        {
            int value = 10;
            printf("(%i)", value);
            printf("(%d)", 10);
            printf("(%u)(%u)", 12312, 12312);

             return 0;
        }
        """
        self.evaluate(code)
        self.assertEqual(self.stdout.read(), "(10)(10)(12312)(12312)")

    def test_printf_long(self):
        code = """
        #include <stdio.h>

        int main()
        {
            long value = 12412421345324;
            printf("(%li)", value);
            printf("(%ld)", 1152921504606846976L);
            printf("(%lld)(%li)", 0LL, 4770931718827366147L);
            printf("(%lu)(%llu)(%lo)(%llo)(%llx)(%llX)",
                807023UL, 8736574736ULl, 06576374073l, 07743525251lL, 0x243fa8c1ell, 0XAB7A6LL);
            printf("(%llu)", -1LLU);

            return 0;
        }
        """
        self.evaluate(code)
        self.assertEqual(
            self.stdout.read(),
            '(12412421345324)(1152921504606846976)(0)(4770931718827366147)' +
            '(807023)(8736574736)(6576374073)(7743525251)(243fa8c1e)(AB7A6)' +
            '(18446744073709551615)'
        )

    def test_printf_float(self):
        code = """
        #include <stdio.h>

        int main()
        {
            double value = 10.25;
            printf("(%f)", value);
            printf("(%F)", 20.5);
            printf("(%f)(%f)(%f)", 10.25, 10.25, -9.005000000000000329);
            return 0;
        }
        """
        self.evaluate(code)
        self.assertEqual(self.stdout.read(), "(10.25)(20.5)(10.25)(10.25)(-9.00500000000000078)")

    def test_printf_hexadecimal(self):
        code = """
        #include <stdio.h>

        int main()
        {
            int value = 5324;
            printf("(%x)", value);
            printf("(%x)", -1232);
            printf("(%X)(%X)", 982348, -982348);

            return 0;
        }
        """
        self.evaluate(code)
        self.assertEqual(self.stdout.read(), "(14cc)(fffffb30)(EFD4C)(FFF102B4)")

    def test_printf_octal(self):
        code = """
        #include <stdio.h>

        int main()
        {
            int value = 12321;
            printf("%o", value);
            printf("%o%o", 3439, -2342);
            return 0;
        }
        """
        self.evaluate(code)
        self.assertEqual(self.stdout.read(), "30041655737777773332")

    def test_printf_pointer(self):
        code = """
        #include <stdio.h>

        int main()
        {
            void *ptr = (void *)129873;
            printf("%p", ptr);
            printf("%p%p", (void *)43243, (void *)-12434);

            return 0;
        }
        """
        self.evaluate(code)
        self.assertEqual(self.stdout.read(), "0x1fb510xa8eb0xffffffffffffcf6e")