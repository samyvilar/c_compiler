__author__ = 'samyvilar'

from test.test_back_end.test_stdlib.base import TestStdLib


class TestMalloc(TestStdLib):
    def test_malloc_function(self):
        source = """
        #include <stdlib.h>

        int main()
        {
            int *temp = malloc(sizeof(int));
            *temp = 10;
            return *temp;
        }

        """
        super(TestMalloc, self).evaluate(source)

