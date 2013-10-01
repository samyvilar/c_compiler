
/*
    The previous 4 level virtual memory is simply to slow.
    This time around lets create a three tier virtual memory
    A list of blocks each with a list of pages each with a list of
    words ...
    Since we really don't need to (and most cpu's as of today don't) actually
    use all 64 bits to calculate the address we'll use the least significant 48 bits ...
    (which is what is currently used)
*/

#include <string.h>
#include "bit_hash.h"

#define INLINE inline

#define _type_ long long int
#define float_type double
#define WORD_PRINTF_FORMAT "%llu"

#define word_type unsigned _type_
#define signed_word_type signed _type_
// 48 bits
//#define BLOCK_BIT_SIZE 21
//#define PAGE_BIT_SIZE 15
//#define WORD_BIT_SIZE 12

#define BLOCK_BIT_SIZE 24
#define PAGE_BIT_SIZE 12
#define WORD_BIT_SIZE 12


#define NUMBER_OF_BLOCKS ((word_type)1 << (word_type)BLOCK_BIT_SIZE)
#define NUMBER_OF_PAGES ((word_type)1 << (word_type)PAGE_BIT_SIZE)
#define NUMBER_OF_WORDS ((word_type)1 << (word_type)WORD_BIT_SIZE)

#define word_id(addr)  ((addr) & (NUMBER_OF_WORDS - 1))
#define page_id(addr)  (((addr) & ((NUMBER_OF_PAGES - 1) << WORD_BIT_SIZE)) >> WORD_BIT_SIZE)
#define block_id(addr) (((addr) & ((NUMBER_OF_BLOCKS - 1) << (WORD_BIT_SIZE + PAGE_BIT_SIZE))) >> (WORD_BIT_SIZE + PAGE_BIT_SIZE))

/*
    In order to calculate faults we need to zero out the tables, but this is quite expensive
    specially for large tables, so well use a bit hash table to check whether or not
    the entry has being initialized.
*/

#define page_type word_type

#define word(page, word_id) (page + word_id)

typedef struct block_type {
    page_type *pages[NUMBER_OF_PAGES];
    bit_hash_type faults[NUMBER_ELEMENTS(NUMBER_OF_PAGES)];
} block_type;
#define pages(block) ((page_type **)block)
#define page(block, page_id) (*(pages(block) + page_id))
#define set_page(block, page_id, value) (page(block, page_id) = (value))

#define faults(block) ((block)->faults)
#define page_fault(block, page_id) bit_value(faults(block), page_id)
#define clear_page_fault(block, page_id) clear_bit_value(faults(block), page_id)


typedef struct virtual_memory_type {
    block_type *blocks[NUMBER_OF_BLOCKS];
    bit_hash_type faults[NUMBER_ELEMENTS(NUMBER_OF_BLOCKS)];
} virtual_memory_type;
#define blocks(vm) ((block_type **)vm)
#define block(vm, block_id) (*(blocks(vm) + block_id))
#define set_block(vm, block_id, value) (block(vm, block_id) = (value))

#define block_fault page_fault
#define clear_block_fault clear_page_fault

INLINE virtual_memory_type *new_virtual_memory();
INLINE block_type *new_block();
#define new_page() malloc(NUMBER_OF_WORDS * sizeof(word_type))

INLINE word_type *translate_address(virtual_memory_type *vm, word_type addr);

#define get_word(vm, addr) (*translate_address(vm, addr))
#define set_word(vm, addr, value) (get_word(vm, addr) = (value))
