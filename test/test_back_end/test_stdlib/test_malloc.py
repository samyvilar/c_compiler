__author__ = 'samyvilar'

from test.test_back_end.test_stdlib.base import TestStdLib
from front_end.parser.ast.expressions import ConstantExpression, IntegerType


class TestMalloc(TestStdLib):
    def test_malloc_simple(self):
        source = """
        #include <stdlib.h>
        #define TEST_SIZE 10

        int main()
        {
            void *heap_ptr = sbrk(0);
            unsigned char *value = malloc(sizeof(unsigned char) * TEST_SIZE);
            unsigned int index = TEST_SIZE;
            unsigned char *temp = value;

            while (index--)
                *temp++ = 1 - TEST_SIZE;

            index = TEST_SIZE;
            temp = value;

            while (index--)
                if (*temp++ != (unsigned char)(1 - TEST_SIZE))
                    return -2;

            free(value);

            if (heap_ptr != sbrk(0))
                return -1;

            return 0;
        }
        """
        self.evaluate(source)
        self.assert_base_element(ConstantExpression(0, IntegerType()))
        # self.assertEqual(int(self.mem[self.cpu.stack_pointer]), 0)

    def test_malloc_complex(self):
        source = """
        #include <stdlib.h>
        #include <string.h>
        #include <stdio.h>

        #define TEST_SIZE 20
        #define MAX_BLOCK_SIZE 256

        struct __block_type__ {int size; char value; unsigned char *address;};

        void randomly_initialize_block(struct __block_type__ *block)
        {
            block->size = (rand() & (MAX_BLOCK_SIZE - 1));
            block->value = (char)rand();
            block->address = malloc(block->size * sizeof(unsigned char));
            memset(block->address, block->value, block->size * sizeof(unsigned char));
        }

        int main()
        {
            void *initial_heap_pointer = sbrk(0);  // record initial heap pointer ...
            struct __block_type__ allocated_blocks[TEST_SIZE];
            int test_size = TEST_SIZE;

            size_t total_allocation_size = 0;
            while (test_size--) // randomly initialize all the blocks ...
            {
                randomly_initialize_block(&allocated_blocks[test_size]);
                total_allocation_size += allocated_blocks[test_size].size;
            }

            test_size = 2 * TEST_SIZE;
            int index;
            while (test_size--)  // randomly deallocate some of the blocks ...
            {
                index = rand() % TEST_SIZE; // randomly pick a block ...
                free(allocated_blocks[index].address); // deallocate its content ...
                randomly_initialize_block(&allocated_blocks[index]);  // randomly re-initialize its content ...
            }


            test_size = TEST_SIZE;
            while (test_size--)
            {   // check that free/malloc haven't corrupted any other blocks ...
                for (index = 0; index < allocated_blocks[test_size].size; index++)
                    if (allocated_blocks[test_size].address[index] != allocated_blocks[test_size].value)
                        return -1;
                    free(allocated_blocks[test_size].address);  // check was ok, so deallocate it ...
            }

            return sbrk(0) - initial_heap_pointer; // check that deallocating everything has reset the heap pointer...
        }
        """
        self.evaluate(source)
        self.assert_base_element(ConstantExpression(0, IntegerType()))
        # self.assertEqual(self.mem[self.cpu.stack_pointer], 0)