#include <stdlib.h>
#include <stdio.h>
#include <unistd.h>
#include "fast_vm.h"

void test_virtual_memory()
{
    struct virtual_memory_type *vm = new_virtual_memory();

#define TEST_LENGTH 500000
    unsigned int
            number_of_tests = TEST_LENGTH,
            int_index;
    word_type *words = malloc(sizeof(word_type) * TEST_LENGTH);

#define _addr(base, offset) base[offset]
#define _value _addr
    printf("setting ...\n");
    while (number_of_tests--)
    {
        int_index = sizeof(word_type)/sizeof(int);
        while (int_index--)
            ((int *)(&words[number_of_tests]))[int_index] = rand();

        set_word(vm, _addr(words, number_of_tests), _value(words, number_of_tests));
        if (get_word(vm, _addr(words, number_of_tests)) !=  _value(words, number_of_tests))
        {
            printf("test # %u: failed to set word " WORD_PRINTF_FORMAT " at " WORD_PRINTF_FORMAT "\n",
                    number_of_tests, _value(words, number_of_tests), _addr(words, number_of_tests));
            exit(-1);
        }
    }
    printf("verifying ...\n");
    number_of_tests = TEST_LENGTH;
    while (number_of_tests--)
        if (get_word(vm, _addr(words, number_of_tests)) != _value(words, number_of_tests))
        {
            printf("test #%u: failed to set word " WORD_PRINTF_FORMAT " at " WORD_PRINTF_FORMAT " got " WORD_PRINTF_FORMAT "\n",
                    number_of_tests,
                    _value(words, number_of_tests),
                    _addr(words, number_of_tests),
                    get_word(vm, _addr(words, number_of_tests))
            );
            exit(-1);
        }
#undef _addr
#undef _value
}

int main()
{
    printf("Testing Virtual Memory ... \n");
    test_virtual_memory();
    printf("done\n");

    return 0;
}