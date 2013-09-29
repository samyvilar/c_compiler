/*****************************************************************************************************
  * Four level paged virtual memory ... shelf -> Book -> Page -> Word
  *
  * we can either use % / + => (addr / TOTAL_SIZE) + (addr % TOTAL_SIZE) to calculate each offset but
  * the % and / are quite expensive, so we'll just segment the address ino 4 two byte offsets
  * where:
  * the first two bytes is the word index or id,
  * the second two bytes is the page index or id,
  * the third two bytes is the book index or id,
  * the fourth two bytes is the shelf index or id ...
  * this may be faster/simpler but a shelf fault will consume, at a minimum, 8*2**16 = 524288 Byte overhead ...
  * not to mention making random access a complete disaster since it would generate fault after fault but
  * a fault would most probably halt the machine ... on average the stack and heap move continuously in each
  * of their perspective directions ...
*******************************************************************************************************/
#include <stdio.h>
#include "virtual_memory.h"

INLINE virtual_memory_type *new_virtual_memory(word_type shelf_size) {
    return calloc(shelf_size, sizeof(shelf_type *));
}

#define malloc sbrk
#define calloc(quantity, size) (memset(malloc(quantity * size), 0, quantity * size))
// allocate space for the addresses of the shelves, this should only be called once for each cpu or process
//#define new_virtual_memory(quantity) calloc(quantity, sizeof(shelf_type *))
#define new_shelf(quantity) calloc(quantity, sizeof(book_type *))
#define new_book(quantity) calloc(quantity, sizeof(page_type *))
#define new_page(quantity) malloc(quantity * sizeof(word_type)) // no need to (costly) zero out the actual page ...
#undef malloc
#undef calloc

INLINE shelf_type *shelf(virtual_memory_type *vm, word_type addr)
{
    shelf_type **curr_shelf = (vm + shelf_id(addr));  // vm is a list of shelve pointers ...
    if (!*curr_shelf)  // shelf fault, no shelf has being allocated for this address so allocate a new one ...
        *curr_shelf = new_shelf(NUMBER_OF_BOOKS);
    return *curr_shelf; // return base address of shelf ...
}
//#define shelf(vm, addr) (*(vm + shelf_id(addr)) ? *(vm + shelf_id(addr)) : (*(vm + shelf_id(addr)) = new_shelf(NUMBER_OF_BOOKS)))

INLINE book_type *book(shelf_type *shelf, word_type addr)
{
    book_type **curr_book = (shelf + book_id(addr));  // a shelf is a list of book pointers ...
    if (!*curr_book) // book fault ...
        *curr_book = new_book(NUMBER_OF_PAGES);
    return *curr_book;
}
//#define book(shelf, addr) (*(shelf + book_id(addr)) ? *(shelf + book_id(addr)) : (*(shelf + book_id(addr)) = new_book(NUMBER_OF_PAGES)))

INLINE page_type *page(book_type *book, word_type addr)
{
    page_type **curr_page = (book + page_id(addr)); // a book is a list of page pointers ...
    if (!*curr_page)  // page fault ...
        *curr_page = new_page(NUMBER_OF_WORDS);
    return *curr_page;
}
//#define page(book, addr) (*(book + page_id(addr)) ? *(book + page_id(addr)) : (*(book + page_id(addr)) = new_page(NUMBER_OF_WORDS)))


INLINE void _set_word_(virtual_memory_type *mem, word_type address, word_type value) {
    set_word(mem, address, value);
}
INLINE word_type _get_word_(virtual_memory_type *mem, word_type address) {
    return get_word(mem, address);
}

void initialize_virtual_memory(virtual_memory_type *mem, word_type *address, word_type *values, word_type amount)
{
    while (amount--)
        set_word(mem, *address, *values), ++address, ++values;
}