__author__ = 'samyvilar'

from test.test_back_end.test_stdlib.base import TestStdLib


class TestString(TestStdLib):
    test_size = 10

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
        #define TEST_SIZE 20

        int main()
        {{
            int guard_0 = 0;
            int src[TEST_SIZE] = {{[0 ... TEST_SIZE/2] = -1, [(TEST_SIZE/2) + 1 ... TEST_SIZE - 1] = 1}};
            int guard_1 = 0;

            if (memmove(src, &src[TEST_SIZE/2], (TEST_SIZE/2)*sizeof(int)) != src)
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
            int prev[10];
            int guard_1 = -1;
            int curr[20];
            int guard_2 = -1;
            int next[30];
            int guard_3 = -1;

            if (memset(prev, 0, sizeof(prev)) != prev)
                return -1;
            if (memset(curr, -1, sizeof(curr)) != curr)
                return -1;
            if (memset(next, 1, sizeof(next)) != next)
                return -1;

            int index = 0;
            for (index = 0; index < sizeof(prev)/sizeof(prev[0]); index++)
                if (prev[index] != 0)
                    return -2;

            for (index = 0; index < sizeof(curr)/sizeof(curr[0]); index++)
                if (curr[index] != -1)
                    return -3;

            for (index = 0; index < sizeof(next)/sizeof(next[0]); index++)
                if (next[index] != 1)
                    return -4;

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
            while (index < sizeof(src)/sizeof(src[0]))
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
            strncpy(dest, "test", 0);
            strncpy(dest, src, 0);

            if (dest[0] != 'g')
                return -1;

            if (src[0] != 't')
                return -2;

            if (strncpy(dest, src, (sizeof(src)/sizeof(src[0])) - 1) != dest)
                return -1;
            if (src[0] != 't')
                return -2;

            size_t index = -1, length = strlen(dest);
            while (++index < length)
                if (src[index] != dest[index])
                    return dest[index];

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
            while (index < sizeof(result)/sizeof(result[0]))
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

            if (strncat(initial, " there", strlen(" there")) != initial)
                return -1;

            char result[12] = "hello there";
            size_t index = 0;
            while (index < strlen("hello there"))
                if ("hello there"[index] != initial[index++])
                    return -index;

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

            if (strcmp(temp, temp) || strcmp("", "") || strcmp("", "a") > 0) //|| strcmp("a", "") < 0)
                return -1;

            if (strcmp(temp, "this is a test."))
                return -1;

            return 1;
        }
        """
        self.evaluate(code)
        self.assertEqual(int(self.mem[self.cpu.stack_pointer]), 1)

    def test_strncmp(self):
        code = """
        #include <string.h>

        int main()
        {
            char temp[50] = "this is a test.";

            if (strncmp("a", "c", 0) || strncmp(NULL, NULL, 0) || strncmp("", "", 0) || strncmp("ab", "ac", 0))
                return -1;

            if (strncmp(temp, "this", strlen("this") - 1) || strncmp(temp, temp, (sizeof(temp)/sizeof(char)) * 2))
                return -1;

            return 1;
        }
        """
        self.evaluate(code)
        self.assertEqual(int(self.mem[self.cpu.stack_pointer]), 1)

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
        self.assertEqual(int(self.mem[self.cpu.stack_pointer]), 1)

    def test_strcspn(self):
        code = """
        #include <string.h>

        int main()
        {
            char temp[50] = "this is a test.";

            if (strcspn("", "") || strcspn("asds", "a"))
                return -1;

            if (strcspn(temp, ".") != strlen(temp) - 1)
                return -1;

            return 1;
        }
        """
        self.evaluate(code)
        self.assertEqual(int(self.mem[self.cpu.stack_pointer]), 1)

    def test_strpbrk(self):
        code = """
        #include <string.h>

        int main()
        {
            char temp[50] = "this is a test ...";

            if (strpbrk("", "") || strpbrk("hello", "")  || strpbrk("", "23423") || strpbrk("12323", "asd"))
                return -1;

            if (strpbrk(temp, "12af.") != (temp + 8))
                return -1;

            return 1;
        }
        """
        self.evaluate(code)
        self.assertEqual(int(self.mem[self.cpu.stack_pointer]), 1)

    def test_strrchr(self):
        code = """
        #include <string.h>

        int main()
        {
            char temp[50] = "this is a test ...";
            char *empty = "";
            if (strrchr(empty, '\0') != empty || strrchr("", 'a'))
                return -1;

            if (strrchr(temp, '.') != temp + strlen(temp) - 1 ||
                strrchr(temp, '\0') != temp + strlen(temp)
            )
                return -1;

            return 1;
        }
        """
        self.evaluate(code)
        self.assertEqual(int(self.mem[self.cpu.stack_pointer]), 1)

    def test_strspn(self):
        code = """
        #include <string.h>

        int main()
        {
            char temp[50] = "this is a test ...";

            if (strspn("asdas", "") || strspn("asdsad", "12123") || strspn("", "asds"))
                return -1;

            if (strspn(temp, temp) != strlen(temp) || strspn(temp, "this") != strlen("this"))
                return -2;

            if (strspn("hello", "hello") != strlen("hello"))
                return -1;

            return 1;
        }
        """
        self.evaluate(code)
        self.assertEqual(int(self.mem[self.cpu.stack_pointer]), 1)

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

            if (strstr(temp, "this") != temp || strstr(temp, "...") != temp + strlen("this ..is .a test "))
                return -1;

            return 1;
        }
        """
        self.evaluate(code)
        self.assertEqual(int(self.mem[self.cpu.stack_pointer]), 1)

    def test_a_strtok(self):
        code = """
        #include <string.h>
        #include <stdio.h>

        int main()
        {
            char temp[22] = "this 1 is 2a test ...";
            char *current;

            if (strtok("", "") || strtok("", "., "))
                return -1;

            current = strtok(temp, " ");
            if (current != temp || strlen(current) != 4)
                return -strlen(current);

            current = strtok(NULL, " ");
            if (*current != '1' || strlen(current) != 1)
                return -3;

            current = strtok(NULL, "s i");
            if (*current != '2' || strlen(current) != 2)
                return -10;


            current = strtok(NULL, "");
            if (*current != 't')
                return temp - current;

            if (strtok(NULL, " "))
                return -5;

            return 1;
        }
        """
        self.evaluate(code)
        self.assertEqual(int(self.mem[self.cpu.stack_pointer]), 1)

    def test_strlen(self):
        code = """
        #include <string.h>

        int main()
        {
            if (strlen("a") != 1)
                return -1;

            if (strlen(""))
                return -2;

            char temp[50] = "this is a test ...";

            if (strlen(temp) != ((sizeof("this is a test ...")/sizeof(char)) - 1)) // subtract one to account for '\0'
                return -3;

            if (strlen("\0asdasd"))
                return -5;

            return 1;
        }
        """
        self.evaluate(code)
        self.assertEqual(int(self.mem[self.cpu.stack_pointer]), 1)