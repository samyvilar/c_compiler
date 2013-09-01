__author__ = 'samyvilar'

from test.test_back_end.test_stdlib.base import TestStdLib


class TestString(TestStdLib):
    test_size = 36

    def evaluate(self, code):
        super(TestString, self).evaluate(code)

    def test_memcpy(self):
        code = """
        #include <string.h>
        #define TEST_SIZE {test_size}

        int main()
        {{
            int guard_0 = 0;
            int *src[TEST_SIZE] = {{[0 ... TEST_SIZE - 1] = -1}};
            int guard_1 = 0;
            int *dest[TEST_SIZE] = {{[0 ... TEST_SIZE - 1] = 1}};
            int guard_2 = 0;

            if (memcpy(dest, src, sizeof(src)) != dest)
                return -1;

            int index = TEST_SIZE;
            while (index--)
                if (dest[index] != src[index])
                    return -1;

            return !(guard_0 || guard_1 || guard_2);
        }}
        """.format(test_size=TestString.test_size)
        self.evaluate(code)
        self.assertEqual(self.mem[self.cpu.stack_pointer], 1)

    def test_memmove(self):
        code = """
        #include <string.h>
        #define TEST_SIZE {test_size}

        int main()
        {{
            int guard_0 = 0;
            int src[TEST_SIZE] = {{[0 ... TEST_SIZE - 1] = -1}};
            int guard_1 = 0;
            int dest[TEST_SIZE] = {{[0 ... TEST_SIZE - 1] = 1}};
            int guard_2 = 0;

            if (memmove(dest, src, sizeof(src)) != dest)
                return -1;

            int index = TEST_SIZE;
            while (index--)
                if (src[index] != dest[index])
                    return -1;

            return !(guard_0 || guard_1 || guard_2);
        }}
        """.format(test_size=TestString.test_size)
        self.evaluate(code)
        self.assertEqual(self.mem[self.cpu.stack_pointer], 1)

    def test_memmove_overlap(self):
        code = """
        #include <string.h>
        #define TEST_SIZE {test_size}

        int main()
        {{
            int guard_0 = 0;
            int src[TEST_SIZE] = {{[0 ... TEST_SIZE/2] = -1, [TEST_SIZE/2 + 1 ... TEST_SIZE - 1] = 1}};
            int guard_1 = 0;

            if (memmove(src, &src[TEST_SIZE/2], TEST_SIZE/2) != src)
                return -1;

            int index = 0;
            while (index < TEST_SIZE/2)
                if (src[index] != src[TEST_SIZE/2 + index++])
                    return -1;

            return !(guard_0 || guard_1);
        }}
        """.format(test_size=TestString.test_size)
        self.evaluate(code)
        self.assertEqual(self.mem[self.cpu.stack_pointer], 1)

    def test_memcmp_equal(self):
        code = """
        #include <string.h>
        #define TEST_SIZE {test_size}
        int main()
        {{
            int guard_0 = 0;
            int values_0[TEST_SIZE] = {{[0 ... TEST_SIZE - 1] = -1}};
            int guard_1 = 0;
            int values_1[TEST_SIZE] = {{[0 ... TEST_SIZE - 1] = -1}};
            int guard_2 = 0;

            return !memcmp(values_0, values_1, sizeof(values_0));
        }}
        """.format(test_size=TestString.test_size)
        self.evaluate(code)
        self.assertEqual(self.mem[self.cpu.stack_pointer], 1)

    def test_memcmp_less_than(self):
        code = """
        #include <string.h>
        #define TEST_SIZE {test_size}
        int main()
        {{
            int guard_0 = 0;
            int values[TEST_SIZE] = {{[0 ... TEST_SIZE/2] = 1, [TEST_SIZE/2 + 1 ... TEST_SIZE - 1] = 2}};
            int guard_1 = 0;

            return memcmp(values, &values[TEST_SIZE/4], sizeof(values)/2) < 0;
        }}
        """.format(test_size=TestString.test_size)
        self.evaluate(code)
        self.assertEqual(self.mem[self.cpu.stack_pointer], 1)

    def test_memcmp_greater_than(self):
        code = """
        #include <string.h>
        #define TEST_SIZE {test_size}
        int main()
        {{
            int guard_0 = 0;
            int values[TEST_SIZE] = {{[0 ... TEST_SIZE/2] = 2, [TEST_SIZE/2 + 1 ... TEST_SIZE - 1] = 1}};
            int guard_1 = 0;

            return memcmp(values, &values[TEST_SIZE/4], sizeof(values)/2) > 0;
        }}
        """.format(test_size=TestString.test_size)
        self.evaluate(code)
        self.assertEqual(self.mem[self.cpu.stack_pointer], 1)

    def test_memchr_located(self):
        code = """
        #include <string.h>
        #define TEST_SIZE {test_size}

        int main()
        {{
            int values[TEST_SIZE] = {{[0 ... TEST_SIZE - 1] = -1}};
            int *loc = &values[TEST_SIZE/2];
            *loc = 1;

            return memchr(values, *loc, sizeof(values)) == loc;
        }}
        """.format(test_size=TestString.test_size)
        self.evaluate(code)
        self.assertEqual(self.mem[self.cpu.stack_pointer], 1)

    def test_memchr_not_located(self):
        code = """
        #include <string.h>
        #define TEST_SIZE {test_size}

        int main()
        {{
            int values[TEST_SIZE] = {{[0 ... TEST_SIZE - 1] = -1}};
            values[TEST_SIZE/2] = 1;

            return !memchr(values, values[TEST_SIZE/2], sizeof(values)/2);
        }}
        """.format(test_size=TestString.test_size)
        self.evaluate(code)
        self.assertEqual(self.mem[self.cpu.stack_pointer], 1)

    def test_memset(self):
        code = """
        #include <string.h>

        int main()
        {
            int guard_0 = -1;
            int prev[20];
            int guard_1 = -1;
            int curr[60];
            int guard_2 = -1;
            int next[100];
            int guard_3 = -1;

            if (memset(prev, 0, 20) != prev)
                return -1;
            if (memset(curr, -1, 60) != curr)
                return -1;
            if (memset(next, 1, 100) != next)
                return -1;

            int index = 0;
            for (index = 0; index < 100; index++)
            {
                if (index < 20 && prev[index] != 0)
                    return -1;
                if (index < 60 && curr[index] != -1)
                    return -1;
                if (next[index] != 1)
                    return -1;
            }


            return guard_0 == -1 && guard_1 == -1 && guard_2 == -1 && guard_3 == -1;
        }
        """
        self.evaluate(code)
        self.assertEqual(self.mem[self.cpu.stack_pointer], 1)

    def test_strcpy(self):
        code = """
        #include <string.h>

        int main()
        {
            int guard_0 = 0;
            char src[19] = "this is a test ...";
            int guard_1 = 0;
            char dest[19] = {[0 ... 18] = 'g'};
            int guard_2 = 0;

            strcpy(dest, "");
            if (dest[0] != '\0')
                return -1;

            if (strcpy(dest, src) != dest)
                return -1;

            size_t index = 0;
            while (index < sizeof(src))
                if (src[index] != dest[index++])
                    return -1;

            return !(guard_0 || guard_1 || guard_2);
        }
        """
        self.evaluate(code)
        self.assertEqual(self.mem[self.cpu.stack_pointer], 1)

    def test_strncpy(self):
        code = """
        #include <string.h>

        int main()
        {
            int guard_0 = 0;
            char src[50] = "this is a test ...";
            char dest[50] = {[0 ... 49] = 'g'};
            int guard_1 = 0;

            strncpy(dest, NULL, 0);
            if (dest[0] != 'g')
                return -1;

            if (strncpy(dest, src, sizeof(src)) != dest)
                return -1;

            size_t index = 0;
            while (index < sizeof(dest))
                if (src[index] != dest[index++])
                    return -1;

            return !(guard_0 || guard_1);
        }
        """
        self.evaluate(code)
        self.assertEqual(self.mem[self.cpu.stack_pointer], 1)

    def test_strcat(self):
        code = """
        #include <string.h>

        int main()
        {
            int guard_0 = 0;
            char initial[12] = "hello";
            int guard_1 = 0;
            char rest[6] = " there";
            int guard_2 = 0;
            char result[12] = "hello there";

            strcat(initial, "");
            if (initial[0] != result[0])
                return -1;

            if (strcat(initial, rest) != initial)
                return -1;

            size_t index = 0;
            while (index < sizeof(result))
                if (initial[index] != result[index++])
                    return -1;
            return !(guard_0 || guard_1 || guard_2);
        }
        """
        self.evaluate(code)
        self.assertEqual(self.mem[self.cpu.stack_pointer], 1)

    def test_strncat(self):
        code = """
        #include <string.h>

        int main()
        {
            int guard_0 = 0;
            char initial[20] = "hello";
            int guard_1 = 0;

            strncat(initial, NULL, 0);
            if (initial[0] != 'h')
                return -1;

            if (strncat(initial, " there", sizeof(" there") - 1) != initial)
                return -1;

            char result[12] = "hello there";
            size_t index = 0;
            while (index < sizeof("hello there"))
                if ("hello there"[index] != initial[index++])
                    return -1;

            return !(guard_0 || guard_1);
        }
        """
        self.evaluate(code)
        self.assertEqual(self.mem[self.cpu.stack_pointer], 1)

    def test_strcmp(self):
        code = """
        #include <string.h>

        int main()
        {
            char temp[50] = "this is a test.";

            if (strcmp(temp, temp) || strcmp("", "") || strcmp("", "a") > 0 || strcmp("a", "") < 0)
                return -1;

            if (strcmp(temp, "this is a test."))
                return -1;

            return 1;
        }
        """
        self.evaluate(code)
        self.assertEqual(self.mem[self.cpu.stack_pointer], 1)

    def test_strncmp(self):
        code = """
        #include <string.h>

        int main()
        {
            char temp[50] = "this is a test.";

            if (strncmp("a", "c", 0) || strncmp(NULL, NULL, 0) || strncmp("", "", 0), strncmp("ab", "ac", 1))
                return -1;

            if (strncmp(temp, "this", sizeof("this") - 1) || strncmp(temp, temp, sizeof(temp) * 2))
                return -1;

            return 1;
        }
        """
        self.evaluate(code)
        self.assertEqual(self.mem[self.cpu.stack_pointer], 1)

    def test_strchr(self):
        code = """
        #include <string.h>

        int main()
        {
            char temp[50] = "this is a test.";

            if (strchr("", 'a') || strchr("a b c", '.'))
                return -1;

            if (strchr(temp,  't') != temp || strchr(temp, 's') != (temp + 3))
                return -1;

            return 1;
        }
        """
        self.evaluate(code)
        self.assertEqual(self.mem[self.cpu.stack_pointer], 1)

    def test_strcspn(self):
        code = """
        #include <string.h>

        int main()
        {
            char temp[50] = "this is a test.";

            if (strcspn("", "") || strcspn("asds", "a"))
                return -1;

            if (strcspn(temp, ".") != sizeof("this is a test") - sizeof(char))
                return -1;

            return 1;
        }
        """
        self.evaluate(code)
        self.assertEqual(self.mem[self.cpu.stack_pointer], 1)

    def test_strpbrk(self):
        code = """
        #include <string.h>

        int main()
        {
            char temp[50] = "this is a test ...";

            if (strpbrk("", "") || strpbrk("hello", "")  || strpbrk("", "23423") || strpbrk("12323", "asd"))
                return -1;

            if (strpbrk(temp, "12af.") != (temp + 8 * sizeof(char)))
                return -1;

            return 1;
        }
        """
        self.evaluate(code)
        self.assertEqual(self.mem[self.cpu.stack_pointer], 1)

    def test_strrchr(self):
        code = """
        #include <string.h>

        int main()
        {
            char temp[50] = "this is a test ...";
            char *empty = "";
            if (strrchr(empty, '\0') != empty || strrchr("", 'a'))
                return -1;

            if (strrchr(temp, '.') != temp + 17 ||
                strrchr(temp, '\0') != temp + sizeof("this is a test ...") - sizeof(char)
            )
                return -1;

            return 1;
        }
        """
        self.evaluate(code)
        self.assertEqual(self.mem[self.cpu.stack_pointer], 1)

    def test_strspn(self):
        code = """
        #include <string.h>

        int main()
        {
            char temp[50] = "this is a test ...";

            if (strspn("asdas", "") || strspn("asdsad", "12123") || strspn("", "asds"))
                return -1;

            if (strspn(temp, temp) != sizeof("this is a test ...") - sizeof(char) ||
                strspn(temp, "this") != sizeof("this") - sizeof(char)
            )
                return -2;

            if (strspn("hello", "hello") != sizeof("hello") - sizeof(char))
                return -1;

            return 1;
        }
        """
        self.evaluate(code)
        self.assertEqual(self.mem[self.cpu.stack_pointer], 1)

    def test_strstr(self):
        code = """
        #include <string.h>

        int main()
        {
            char temp[50] = "this ..is .a test ...";

             if (strstr("", "") || strstr("asds", "") || strstr("asds", "zxcx") ||
                    strstr("hello there", "hello there 1")
                )
                return -1;

            if (strstr(temp, "this") != temp || strstr(temp, "...") != temp + sizeof("this ..is .a test ") - 1)
                return -1;

            return 1;
        }
        """
        self.evaluate(code)
        self.assertEqual(self.mem[self.cpu.stack_pointer], 1)

    def test_a_strtok(self):
        code = """
        #include <string.h>

        int main()
        {
            char temp[22] = "this 1 is 2a test ...";
            char *current;

            if (strtok("", "") || strtok("", "., "))
                return -1;

            current = strtok(temp, " ");
            if (current != temp)
                return -1;

            current = strtok(NULL, " ");
            if (*current != '1')
                return -1;
            current = strtok(NULL, "is ");
            if (*current != '2')
                return -1;
            current = strtok(NULL, "");
            if (*current != 't')
                return *current;
            if (strtok(NULL, " "))
                return -4;

            return 1;
        }
        """
        self.evaluate(code)
        self.assertEqual(self.mem[self.cpu.stack_pointer], 1)

    def test_strlen(self):
        code = """
        #include <string.h>

        int main()
        {
            char temp[50] = "this is a test ...";
            if (strlen(""))
                return -1;
            if (strlen(temp) != sizeof("this is a test ...") - 1)
                return -1;
            if (strlen("a") != sizeof(char))
                return -1;
            if (strlen("\0asdasd"))
                return -1;

            return 1;
        }
        """
        self.evaluate(code)
        self.assertEqual(self.mem[self.cpu.stack_pointer], 1)