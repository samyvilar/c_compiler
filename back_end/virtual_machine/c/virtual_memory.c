/*****************************************************************************************************
  * Four level paged virtual memory ... shelf -> Book -> Page -> Word
  *
  * we can either use % / + => (addr / UNIT_SIZE) + (addr % UNIT_SIZE) to calculate each offset but
  * the % and / are quite expensive, so we'll just segment the address ino 4:
  * assuming 64 bit address: two byte offsets
  * assuming 32 bit address: one byte offsets
  * where:
  * the first offset is the word index
  * the second offset is the page index
  * the third offset is the book index
  * the fourth offset is the shelf index
  * this may be faster/simpler but a shelf fault will consume, at a minimum,
  * 8*2**16 = 524288 bytes overhead or (4*2**8 = 1024 bytes)
  * not to mention making random access a complete disaster since it would generate fault after fault but
  * a fault would most probably halt the machine ... on average the stack and heap move continuously in each
  * of their perspective directions ...
*******************************************************************************************************/
#include <stdio.h>
#include "virtual_memory.h"

#define NEW(func_name, obj_type, quantity) INLINE obj_type* func_name() { \
    obj_type *temp = malloc(sizeof(obj_type));      \
    set_all_bits(faults(temp), quantity);           \
    return temp;    \
}

NEW(new_virtual_memory, struct virtual_memory_type, NUMBER_OF_SHELVES)
NEW(new_shelf, shelf_type, NUMBER_OF_SHELVES)
NEW(new_book, book_type, NUMBER_OF_PAGES)
#define new_page() malloc(NUMBER_OF_WORDS * sizeof(word_type))


INLINE void _set_word_(struct virtual_memory_type *mem, word_type address, word_type value) {
    set_word(mem, address, value);
}
INLINE word_type _get_word_(struct virtual_memory_type *mem, word_type address) {
    return get_word(mem, address);
}

void initialize_virtual_memory(struct virtual_memory_type *mem, word_type *address, word_type *values, word_type amount)
{
    while (amount--)
        set_word(mem, *address, *values), ++address, ++values;
}


#ifndef translate_address
INLINE word_type *translate_address(struct virtual_memory_type *vm, word_type addr)
{
    register word_type
        _shelf_id = shelf_id(addr),
        _book_id = book_id(addr),
        _page_id = page_id(addr),
        _word_id = word_id(addr);

    shelf_type *_shelf;
    book_type *_book;
    page_type *_page;

    if (shelf_fault(vm, _shelf_id))
    {
        _shelf = set_shelf(vm, _shelf_id, new_shelf());
        clear_shelf_fault(vm, _shelf_id);
    }
    else
        _shelf = shelf(vm, _shelf_id);

    if (book_fault(_shelf, _book_id))
    {
        _book = set_book(_shelf, _book_id, new_book());
        clear_book_fault(_shelf, _book_id);
    }
    else
        _book = book(_shelf, _book_id);


    if (page_fault(_book, _page_id))
    {
        _page = set_page(_book, _page_id, new_page());
        clear_page_fault(_book, _page_id);
    }
    else
        _page = page(_book, _page_id);

    return _page + _word_id;
}
#endif