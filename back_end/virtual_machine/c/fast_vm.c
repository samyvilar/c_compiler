#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <stdio.h>
#include "fast_vm.h"

//#define malloc sbrk
// we won't be de-allocating anything as such use faster sbrk call ...

INLINE virtual_memory_type *new_virtual_memory()
{
    virtual_memory_type *vm = malloc(sizeof(virtual_memory_type));
    set_all_bits(faults(vm), NUMBER_OF_BLOCKS);

    return vm;
}

INLINE block_type *new_block()
{
    block_type *block = malloc(sizeof(block_type));
    set_all_bits(faults(block), NUMBER_OF_PAGES);
    return block;
}

INLINE word_type *translate_address(virtual_memory_type *vm, word_type addr)
{
    register word_type
            _block_id = block_id(addr),
            _page_id = page_id(addr),
            _word_id = word_id(addr);

    register block_type *_block;
    if (block_fault(vm, _block_id))
    {
        _block = new_block();
        set_block(vm, _block_id, _block);
        clear_block_fault(vm, _block_id);
    }
    else
        _block = block(vm, _block_id);

    register page_type *_page;
    if (page_fault(_block, _page_id))
    {
        _page = new_page();
        set_page(_block, _page_id, _page);
        clear_page_fault(_block, _page_id);
    }
    else
        _page = page(_block, _page_id);

    return word(_page, _word_id);
}

INLINE void _set_word_(virtual_memory_type *mem, word_type address, word_type value) {
    set_word(mem, address, value);
}
INLINE word_type _get_word_(virtual_memory_type *mem, word_type address) {
    return get_word(mem, address);
}