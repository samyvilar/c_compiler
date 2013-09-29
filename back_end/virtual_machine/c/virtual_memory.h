
#ifndef _VIRTUAL_MEMORY_H_
#define _VIRTUAL_MEMORY_H_

#include <stdlib.h>
#include <unistd.h>
#include <string.h>

// define functions inline or not, gcc will take this as a suggestion (BUT clang WILL FAIL TO LINK)
#define INLINE inline

#define _type_ long long int
#define float_type double
#define vm_index_type unsigned short
#define WORD_PRINTF_FORMAT "%llu"

#define word_type unsigned _type_
#define signed_word_type signed _type_

#define page_type word_type
#define book_type page_type *
#define shelf_type book_type *
#define virtual_memory_type shelf_type *

#define word_id_mask ((word_type)(vm_index_type)-1)
#define page_id_mask (word_id_mask << (8*sizeof(vm_index_type)))
#define book_id_mask (page_id_mask << (8*sizeof(vm_index_type)))
#define shelf_id_mask (book_id_mask << (8*sizeof(vm_index_type)))

#define word_id(addr)  ( (addr) & word_id_mask)
#define page_id(addr)  (((addr) & page_id_mask) >> 8*sizeof(vm_index_type))
#define book_id(addr)  (((addr) & book_id_mask) >> 2*8*sizeof(vm_index_type))
#define shelf_id(addr) (((addr) & shelf_id_mask) >> 3*8*sizeof(vm_index_type))

#define NUMBER_OF_WORDS ((vm_index_type)-1)
#define NUMBER_OF_PAGES NUMBER_OF_WORDS
#define NUMBER_OF_BOOKS NUMBER_OF_PAGES
#define NUMBER_OF_SHELVES NUMBER_OF_BOOKS

INLINE virtual_memory_type *new_virtual_memory(word_type);
INLINE shelf_type *shelf(virtual_memory_type *vm, word_type addr);
INLINE book_type *book(shelf_type *shelf, word_type addr);
INLINE page_type *page(book_type *book, word_type addr);

INLINE void initialiaze_virtual_memory(virtual_memory_type *, word_type *, word_type *, word_type);


#define translate_address(vm, addr) (page(book(shelf((vm), (addr)), (addr)), (addr)) + word_id((addr)))
#define get_word(vm, addr) (*translate_address(vm, addr))
#define set_word(vm, addr, value) ((get_word(vm, addr)) = (value))

// TODO: implement.
void dealloc_virtual_memory(virtual_memory_type *);
void dealloc_shelf(shelf_type *);
void dealloc_book(book_type *);
void dealloc_page(page_type *);

#endif