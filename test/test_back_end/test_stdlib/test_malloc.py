__author__ = 'samyvilar'

from test.test_back_end.test_stdlib.base import TestStdLib


class TestMalloc(TestStdLib):
    def test_malloc(self):
        source = """
        #include <stdlib.h>
        #include <string.h>
        #include <stdio.h>

        #define TEST_SIZE 1
        #define MAX_BLOCK_SIZE 1024

        struct block_type {int size; char value; void *address;};
        void set_block(struct block_type *block)
        {
            block->size = rand() % MAX_BLOCK_SIZE;
            block->value = (char)rand();
            block->address = malloc(block->size);
            memset(block->address, block->value, block->size);
        }

        int main()
        {
            void *initial_heap_pointer = sbrk(0);
            struct block_type allocated_blocks[TEST_SIZE];
            int test_size = TEST_SIZE;
            while (test_size--)
                set_block(&allocated_blocks[test_size]);

            test_size = 2 * TEST_SIZE;
            int index;
            while (test_size--)
            {
                index = rand() % TEST_SIZE;
                free(allocated_blocks[index].address);
                set_block(&allocated_blocks[index]);
            }

            test_size = TEST_SIZE;
            while (test_size--)
            {
                for (index = 0; index < allocated_blocks[test_size].size; index++)
                    if (*(char *)(allocated_blocks[test_size].address + index) !=
                        allocated_blocks[test_size].value)
                        return -1;
                free(allocated_blocks[test_size].address);
            }

            return initial_heap_pointer == sbrk(0);
        }
        """
        self.evaluate(source)
        self.assertEqual(self.mem[self.cpu.stack_pointer], 1)