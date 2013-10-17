
/*
    The previous 4 level virtual memory is simply to slow.
    This time around lets create a three tier virtual memory
    A list of blocks each with a list of pages each with a list of
    words ...
    Since we really don't need to (and most cpu's as of today don't) actually
    use all 64 bits to calculate the address we'll use the least significant 48 bits or lower ...
    (which is currently used)
*/

#include <string.h>
#include <unistd.h>
#include <stdlib.h>
#include <sys/mman.h>

#include "bit_hash.h"
#include "word_type.h"

// #define SYS_PAGE_SIZE 4096

// 48 bits
//#define BLOCK_BIT_SIZE 21
//#define PAGE_BIT_SIZE 15
//#define WORD_BIT_SIZE 12

// 32 bit address space.
#define BLOCK_BIT_SIZE 16
#define PAGE_BIT_SIZE 7
#define WORD_BIT_SIZE 9 // 1 Page, (1 << 9) == 512 == (4096/8) assuming word_type is 8 bytes
#define ARE_LEVEL_SIZES_EQUAL ((BLOCK_BIT_SIZE == PAGE_BIT_SIZE) && (BLOCK_BIT_SIZE == WORD_BIT_SIZE) && (PAGE_BIT_SIZE == WORD_BIT_SIZE))

#define ADDRESS_BIT_SIZE (BLOCK_BIT_SIZE + PAGE_BIT_SIZE + WORD_BIT_SIZE)

#define NUMBER_OF_BLOCKS ((word_type)1 << (word_type)BLOCK_BIT_SIZE)
#define NUMBER_OF_PAGES ((word_type)1 << (word_type)PAGE_BIT_SIZE)
#define NUMBER_OF_WORDS ((word_type)1 << (word_type)WORD_BIT_SIZE)

#define WORD_ID_MASK (NUMBER_OF_WORDS - 1)
#define PAGE_ID_MASK ((NUMBER_OF_PAGES - 1) << WORD_BIT_SIZE)
//(addr & (((1 << block_bit_size) - 1) << (page_bit_size + word_bit_size))) >> (page_bit_size + word_bit_size

#define BLOCK_ID_MASK ((NUMBER_OF_BLOCKS - 1) << (PAGE_BIT_SIZE + WORD_BIT_SIZE))
// Since data tends to be local, the higher bits should not change often.

#define word_id(addr)  ((addr) & WORD_ID_MASK)
#define page_id(addr)  (((addr) & PAGE_ID_MASK) >> ((word_type)WORD_BIT_SIZE))
#define block_id(addr) (((addr) & BLOCK_ID_MASK) >> ((word_type)WORD_BIT_SIZE + (word_type)PAGE_BIT_SIZE))

/*
    In order to calculate faults we need to zero out the tables, but this is quite expensive
    specially for large tables, so well use a bit hash table to check whether or not
    the entry has being initialized.
*/

#define page_type word_type
#define PAGE_POOL_SIZE 10000 // (10000 * 4096)/1000000.0 == 40.96 megabytes.
extern page_type (*page_pool)[PAGE_POOL_SIZE][NUMBER_OF_WORDS];
extern word_type available_pages;

#define word(page, word_id) ((word_type **)page + word_id)

typedef struct block_type {
    page_type *pages[NUMBER_OF_PAGES];
    bit_hash_type faults[NUMBER_ELEMENTS(NUMBER_OF_PAGES)];
} block_type;
#define pages(block) ((page_type **)block)
#define page(block, page_id) (pages(block)[page_id])
#define set_page(block, page_id, value) (page(block, page_id) = (value))

#define faults(block) ((block)->faults)
#define page_fault(block, page_id) bit_value(faults(block), page_id)
#define clear_page_fault(block, page_id) clear_bit_value(faults(block), page_id)

#define BLOCK_POOL_SIZE 10000 // ((1 << 7)*8) + ((1 << 7)/8) == 1040 bytes,  (10000 * 1040)/1000000.0 == 10.4 megabytes
extern block_type *block_pool;
extern word_type available_blocks;

// ((1 << 16) * 8) + ((1 << 16) / 8) + (2 * (1 << 12) * 8) == 598016, 598016/1000000.0 == .59 megabytes
#define CACHE_SIZE ((word_type)(1 << 12))
struct virtual_memory_type {
    block_type *blocks[NUMBER_OF_BLOCKS];
    bit_hash_type faults[NUMBER_ELEMENTS(NUMBER_OF_BLOCKS)];
    word_type cache[CACHE_SIZE][2];
};
#define blocks(vm) ((block_type **)vm)

#define block(vm, block_id) ((blocks(vm)[block_id]))
#define set_block(vm, block_id, value) (block(vm, block_id) = (value))

#define cache(vm) ((vm)->cache)
#define hash(addr) (addr & (CACHE_SIZE - 1))
#define is_address_cached(vm, addr, _hash) (cache(vm)[_hash][0] == (addr))
#define cached_address(vm, hash_value) ((word_type *)(cache(vm)[hash_value][1]))
#define set_cached_address(vm, addr, hash_value, translated_addr) (\
    (cache(vm)[(hash_value)][0] = (addr)), (word_type *)(cache(vm)[(hash_value)][1] = (word_type)(translated_addr))    \
)

#define block_fault page_fault
#define clear_block_fault clear_page_fault

INLINE struct virtual_memory_type *new_virtual_memory();
INLINE block_type *new_block();

#define new_page()   malloc(NUMBER_OF_WORDS * sizeof(word_type))
#define _new_page_inline() ((available_pages) ? (((*page_pool)[--available_pages])) : (new_page()))

#define _new_block_inline(dest)                                         \
    if (available_blocks)                                               \
        dest = block_pool + --available_blocks;                         \
    else                                                                \
    {                                                                   \
        dest = malloc(sizeof(block_type));                              \
        set_all_bits(faults((block_type *)dest), NUMBER_OF_PAGES);      \
    }


#define get_word(vm, addr) (*translate_address(vm, addr))
#define set_word(vm, addr, value) (get_word(vm, addr) = (value))

#define TRANSLATE_ADDRESS_INLINE(       \
    mem_var,                            \
    addr_var,                           \
    dest_var,                           \
    hash_var,                           \
    temp_var                            \
) {                                                                         \
    hash_var = hash(addr_var);                                              \
    if (is_address_cached(mem_var, addr_var, hash_var))                     \
        dest_var = (word_type)cached_address(mem_var, hash_var);            \
    else \
    {                                                                  \
        dest_var = block_id(addr_var);                                      \
        if (block_fault(mem_var, dest_var))                                 \
        {                                                                   \
            _new_block_inline(temp_var);                                    \
            set_block(mem_var, dest_var, temp_var);                         \
            clear_block_fault(mem_var, dest_var);                           \
        }                                                                   \
        else                                                                \
            temp_var = block(mem_var, dest_var);                                    \
        dest_var = page_id(addr_var);                                               \
        if (page_fault((block_type *)temp_var, dest_var))                           \
        {                                                                           \
            clear_page_fault((block_type *)temp_var, dest_var);                     \
            temp_var = set_page((block_type *)temp_var, dest_var, _new_page_inline());      \
        }                                                                           \
        else                                                                        \
            temp_var = page((block_type *)temp_var, dest_var);                      \
        dest_var = word_id(addr_var);                                               \
        dest_var = (word_type)set_cached_address(mem_var, addr_var, hash_var, word(temp_var, dest_var)); \
    }   \
}


#if defined(__i386__)
    #define load_cached_entry_to_sse _mm_loadl_epi64
    #define convert_sse_to_word _mm_cvtsi128_si32
    #define set1_word_to_sse _mm_set1_epi32
    #define get_cached_entry_from_sse(sse_reg) convert_sse_to_word(_mm_srli_si128(sse_reg, 4))
#elif defined(__x86_64__)
    #define load_cached_entry_to_sse _mm_load_si128
    #define convert_sse_to_word _mm_cvtsi128_si64
    #define set1_word_to_sse _mm_set1_epi64x
    #define get_cached_entry_from_sse(sse_reg) convert_sse_to_word(_mm_srli_si128(sse_reg, 8))
#else
    #error "need x86 type cpu ..."
#endif


// seems to be slower
// virtual address space is less than or equal to 32 bits and each level is a multiple of 8
#define TRANSLATE_ADDRESS_SSE_32(  \
    mem_var,                    \
    addr_var,                   \
    dest_var,                   \
    hash_var,                   \
    temp_var,                   \
    cached_entry_var,           \
    ids_var,                    \
    masks_var                   \
) {                             \
    _hash = hash(addr_var);     \
    ids_var = set1_word_to_sse(addr_var);  \
    cached_entry_var = load_cached_entry_to_sse((__m128i *)(&cache(mem_var)[hash_var][0]));           \
    if (convert_sse_to_word(_mm_xor_si128(cached_entry_var, ids_var)))  \
    {   \
        ids_var = _mm_set1_epi32((unsigned int)addr_var); \
        ids_var = _mm_srli_si128(   \
            _mm_and_si128(ids_var, masks_var),   \
            ((WORD_BIT_SIZE + PAGE_BIT_SIZE) / BYTE_BIT_SIZE)   \
        ); \
        dest_var = _mm_cvtsi128_si32(_ids);                 \
        if (block_fault(mem_var, dest_var))                 \
        {                                                   \
            _new_block_inline(temp_var);            \
            set_block(mem_var, dest_var, temp_var);             \
            clear_block_fault(mem_var, dest_var);               \
        }                                                       \
        else                                                    \
            temp_var = block(mem_var, dest_var);                      \
        \
        ids_var = _mm_srli_si128(   \
            _mm_shuffle_epi32(  \
                _mm_srli_si128(ids_var, (4 - ((WORD_BIT_SIZE + PAGE_BIT_SIZE) / BYTE_BIT_SIZE))), \
                _MM_SHUFFLE(3, 2, 0, 1) \
            ),  \
            (WORD_BIT_SIZE / BYTE_BIT_SIZE) \
        ); \
        dest_var = _mm_cvtsi128_si32(ids_var);          \
        if (page_fault((block_type *)temp_var, dest_var)) \
        {               \
            clear_page_fault((block_type *)temp_var, dest_var); \
            temp_var = set_page((block_type *)temp_var, dest_var, new_page());   \
        }           \
        else        \
            temp_var = page((block_type *)temp_var, dest_var);    \
        \
        ids_var = _mm_shuffle_epi32(    \
            _mm_srli_si128(ids_var, (4 - (WORD_BIT_SIZE / BYTE_BIT_SIZE))), \
            _MM_SHUFFLE(3, 2, 0, 1) \
        ); \
        dest_var = _mm_cvtsi128_si32(_ids); \
        dest_var = (word_type)set_cached_address(mem_var, addr_var, hash_var, word(temp_var, dest_var));   \
    }   \
    else    \
        dest_var =  get_cached_entry_from_sse(cached_entry_var);    \
}
 // Address bit space is greater than 32 bits and each level is a multiple of 8
#define TRANSLATE_ADDRESS_SSE_64(   \
    mem_var,                    \
    addr_var,                   \
    dest_var,                   \
    hash_var,                   \
    temp_var,                   \
    cached_entry_var,           \
    ids_var,                    \
    masks_var                   \
) {                             \
    _hash = hash(addr_var);     \
    ids_var = set1_word_to_sse(addr_var);  \
    cached_entry_var = load_cached_entry_to_sse((__m128i *)(&cache(mem_var)[hash_var][0]));           \
    if (convert_sse_to_word(_mm_xor_si128(cached_entry_var, ids_var)))  \
    {   \
        ids_var = _mm_and_si128(ids_var, masks_var);    \
        ids_var = _mm_srli_si128(ids_var, (WORD_BIT_SIZE / BYTE_BIT_SIZE)); \
        temp_var = (void *)_mm_cvtsi128_si64(ids_var); \
        ids_var = _mm_srli_si128(ids_var, 8 + (PAGE_BIT_SIZE / BYTE_BIT_SIZE)); \
        dest_var = _mm_cvtsi128_si64(ids_var);    \
        ids_var = _mm_set1_epi64x((word_type)temp_var);    \
        if (block_fault(mem_var, dest_var))                 \
        {                                                   \
            _new_block_inline(temp_var);            \
            set_block(mem_var, dest_var, temp_var);             \
            clear_block_fault(mem_var, dest_var);               \
        }                                                       \
        else                                                    \
            temp_var = block(mem_var, dest_var);                      \
        dest_var = _mm_cvtsi128_si64(ids_var);                 \
        if (page_fault((block_type *)temp_var, dest_var))   \
        {               \
            clear_page_fault((block_type *)temp_var, dest_var); \
            temp_var = set_page((block_type *)temp_var, dest_var, new_page());  \
        }   \
        else    \
            temp_var = page((block_type *)temp_var, dest_var);  \
        dest_var = word_id(addr_var);   \
        dest_var = (word_type)set_cached_address(vm, addr_var, hash_var, word(temp_var, dest_var)); \
    }   \
    else    \
        dest_var =  get_cached_entry_from_sse(cached_entry_var);    \
}


INLINE word_type *_translate_address(struct virtual_memory_type *vm, word_type addr);
INLINE word_type *_translate_address_32_sse(struct virtual_memory_type *vm, word_type addr);
INLINE word_type *_translate_address_64_sse(struct virtual_memory_type *vm, word_type addr);

//#if ((BLOCK_BIT_SIZE % 8) || (PAGE_BIT_SIZE % 8) || (WORD_BIT_SIZE % 8))
//    #define translate_address _translate_address
//#else
//// All bit sizes are of mod 8.
//    #if (ADDRESS_BIT_SIZE <= 32)
//        #define translate_address _translate_address_32_sse
//    #elif (ADDRESS_BIT_SIZE <= 64)
//        #define translate_address _translate_address_64_sse
//    #else
//        #define translate_address _translate_address
//    #endif
//#endif

#define translate_address _translate_address



