
#ifndef _VIRTUAL_MEMORY_H_
#define _VIRTUAL_MEMORY_H_

#include <stdlib.h>
#include <unistd.h>
#include <string.h>

#include "word_type.h"
#include "bit_hash.h"

// define functions inline or not, gcc will take this as a suggestion (BUT clang WILL FAIL TO LINK)

#define page_type word_type

#define WORD_INDEX_BIT_SIZE 12
#define PAGE_INDEX_BIT_SIZE 12
#define BOOK_INDEX_BIT_SIZE 12
#define SHELF_INDEX_BIT_SIZE 12

#define NUMBER_OF_WORDS ((word_type)1 << (word_type)WORD_INDEX_BIT_SIZE)
#define NUMBER_OF_PAGES ((word_type)1 << (word_type)PAGE_INDEX_BIT_SIZE)
#define NUMBER_OF_BOOKS ((word_type)1 << (word_type)BOOK_INDEX_BIT_SIZE)
#define NUMBER_OF_SHELVES ((word_type)1 << (word_type)SHELF_INDEX_BIT_SIZE)


//#define book_type page_type *
//#define shelf_type book_type *
//#define virtual_memory_type shelf_type *

typedef struct book_type {
    page_type *pages[NUMBER_OF_PAGES];
    bit_hash_type faults[NUMBER_ELEMENTS(NUMBER_OF_PAGES)];
} book_type;
#define pages(book) ((page_type **)book)
#define page(book, page_id) (*(pages(book) + page_id))
#define set_page(book, page_id, value) (page(book, page_id) = (value))

typedef struct shelf_type {
    book_type *books[NUMBER_OF_BOOKS];
    bit_hash_type faults[NUMBER_ELEMENTS(NUMBER_OF_BOOKS)];
} shelf_type;
#define books(shelf) ((book_type **)shelf)
#define book(shelf, shelf_id) (*(books(shelf) + shelf_id))
#define set_book(shelf, shelf_id, value) (book(shelf, shelf_id) = (value))

struct virtual_memory_type {
    shelf_type *shelves[NUMBER_OF_SHELVES];
    bit_hash_type faults[NUMBER_ELEMENTS(NUMBER_OF_SHELVES)];
};
#define shelves(vm) ((shelf_type **)vm)
#define shelf(vm, shelf_id) (*(shelves(vm) + shelf_id))
#define set_shelf(vm, shelf_id, value) (shelf(vm, shelf_id) = (value))

#define faults(obj) ((obj)->faults)
#define fault(obj, index) (bit_value(faults(obj), index))
#define shelf_fault fault
#define book_fault fault
#define page_fault fault
#define clear_fault(obj, index) (clear_bit_value(faults(obj), index))
#define clear_shelf_fault clear_fault
#define clear_book_fault clear_fault
#define clear_page_fault clear_fault


#define word_id_mask (NUMBER_OF_WORDS - 1)
#define page_id_mask ((NUMBER_OF_PAGES - 1) << WORD_INDEX_BIT_SIZE)
#define book_id_mask ((NUMBER_OF_BOOKS - 1) << (WORD_INDEX_BIT_SIZE + PAGE_INDEX_BIT_SIZE))
#define shelf_id_mask ((NUMBER_OF_SHELVES - 1) << (WORD_INDEX_BIT_SIZE + PAGE_INDEX_BIT_SIZE + BOOK_INDEX_BIT_SIZE))

#define word_id(addr)  ( (addr) & word_id_mask)
#define page_id(addr)  (((addr) & page_id_mask) >> WORD_INDEX_BIT_SIZE)
#define book_id(addr)  (((addr) & book_id_mask) >> (WORD_INDEX_BIT_SIZE + PAGE_INDEX_BIT_SIZE))
#define shelf_id(addr) (((addr) & shelf_id_mask) >> (WORD_INDEX_BIT_SIZE + PAGE_INDEX_BIT_SIZE + BOOK_INDEX_BIT_SIZE))


INLINE struct virtual_memory_type *new_virtual_memory();
INLINE void initialiaze_virtual_memory(struct virtual_memory_type *, word_type *, word_type *, word_type);

//word_type __addr;
//#define translate_address(vm, addr) (page(book(shelf((vm), (addr)), (addr)), (addr)) + word_id((addr)))
//#define translate_address(vm, addr) ((__addr = (addr)), (page(book(shelf((vm), (__addr)), (__addr)), (__addr)) + word_id((__addr))))
INLINE word_type *translate_address(struct virtual_memory_type *vm, word_type addr);
#define get_word(vm, addr) (*translate_address(vm, addr))
#define set_word(vm, addr, value) ((get_word(vm, addr)) = (value))

// TODO: implement.
void dealloc_virtual_memory(struct virtual_memory_type *);
void dealloc_shelf(shelf_type *);
void dealloc_book(book_type *);
void dealloc_page(page_type *);



#endif