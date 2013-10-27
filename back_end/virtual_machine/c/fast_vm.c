#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <stdio.h>
#include "fast_vm.h"

#include "emmintrin.h"

// each block is 1040 bytes assuming (1 << 7) pages
block_type *block_pool = (block_type []){
    [0 ... (BLOCK_POOL_SIZE - 1)].faults[0 ... (NUMBER_ELEMENTS(NUMBER_OF_PAGES) - 1)] = FAULT_ID
};
word_type available_blocks = BLOCK_POOL_SIZE;

page_type (*page_pool)[PAGE_POOL_SIZE][NUMBER_OF_WORDS] = &(page_type [PAGE_POOL_SIZE][NUMBER_OF_WORDS]){};
word_type available_pages = PAGE_POOL_SIZE;


INLINE struct virtual_memory_type *new_virtual_memory()
{
    struct virtual_memory_type *vm = malloc(sizeof(struct virtual_memory_type));
    initialize_faults(faults(vm), NUMBER_OF_BLOCKS);
    initilize_vm_cache(vm);
    return vm;
}

INLINE block_type *new_block()
{
    if (available_blocks)
        return block_pool + --available_blocks;
    
    block_type *block = malloc(sizeof(block_type));
    initialize_faults(faults(block), NUMBER_OF_PAGES);
    return block;
}

INLINE word_type *_translate_address(struct virtual_memory_type *vm, word_type addr)
{
    register word_type _addr, _hash;
    register void *_temp;
    
    TRANSLATE_ADDRESS_INLINE(vm, addr, _addr, _hash, _temp);
    
    return (word_type *)_addr;
}

//INLINE word_type *_translate_address_32_sse(struct virtual_memory_type *vm, word_type addr)
//{ // assume the address bit space does not exceed 32 bits, and all are equal length.
//    
//    register word_type
//        _hash asm("r8"),
//        _trans asm("r9");
//    
//    register void *_temp asm("r10");
//    
//    register __m128i
//        _cached_entry asm("xmm13"),
//        _ids asm ("xmm15"),
//        _masks asm ("xmm14") = _mm_set_epi32(WORD_ID_MASK, PAGE_ID_MASK, 0, BLOCK_ID_MASK);
//    
//    TRANSLATE_ADDRESS_SSE_32(
//        vm,
//        addr,
//        _trans,
//        _hash,
//        _temp,
//        _cached_entry,
//        _ids,
//        _masks
//    );
//    
//    return (word_type *)_trans;
////    #if defined(__i386__)
////        register __m128i _cached_entry asm("xmm13") = _mm_loadl_epi64((__m128i *)(cache(vm) + _hash));
////        if (_mm_cvtsi128_si32(_mm_cmpeq_epi32(_cached_entry, _mm_set1_epi32((unsigned int)addr)))
////            return (word_type *)_mm_cvtsi128_si32(_mm_srli_si128(_cached_entry, 4));
////    #elif defined(__x86_64__)
////        register __m128i _cached_entry asm("xmm13") = _mm_load_si128((__m128i *)(cache(vm) + _hash));
////        if (_mm_cvtsi128_si64(_mm_cmpeq_epi32(_cached_entry, _mm_set1_epi64x(addr))))
////            return (word_type *)_mm_cvtsi128_si64(_mm_srli_si128(_cached_entry, 8));
////    #endif
////            
////    
////    register __m128i
////        _ids asm ("xmm15") = _mm_set1_epi32((unsigned int)addr),
////        // BLOCK bit size (may or should) have a greater range.
////        _masks asm ("xmm14") = _mm_set_epi32(WORD_ID_MASK, PAGE_ID_MASK, 0, BLOCK_ID_MASK);
////    
////    _ids = _mm_and_si128(_ids, _masks);
////    _ids = _mm_srli_si128(_ids, ((WORD_BIT_SIZE + PAGE_BIT_SIZE) / 8));
////    _block_id = _mm_cvtsi128_si32(_ids);
////            
////    if (block_fault(vm, _block_id))
////    {
////        set_block(vm, _block_id, (_block = new_block()));
////        clear_block_fault(vm, _block_id);
////    }
////    else
////        _block = block(vm, _block_id);
////    
////    #define _page_id _block_id
////    // shuffle to make space for shift.
////    _ids = _mm_srli_si128(_ids, (4 - ((WORD_BIT_SIZE + PAGE_BIT_SIZE) / 8))); // shift out the block_id completely
////    _ids = _mm_shuffle_epi32(_ids, _MM_SHUFFLE(3, 2, 0, 1)); // get the page_id
////    _ids = _mm_srli_si128(_ids, WORD_BIT_SIZE / 8);
////    _page_id = _mm_cvtsi128_si32(_ids);
////         
////    if (page_fault((block_type *)_block, _page_id))
////    {
////        clear_page_fault((block_type *)_block, _page_id);
////        #define _page _block
////        _page = set_page((block_type *)_block, _page_id, new_page());
////    }
////    else
////        _page = page((block_type *)_block, _page_id);
////    #undef _page_id
////    
////    
////    #define _word_id _block_id
////    _ids = _mm_srli_si128(_ids, (4 - (WORD_BIT_SIZE / 8))); // shift out the page_id completely
////    _ids = _mm_shuffle_epi32(_ids, _MM_SHUFFLE(3, 2, 0, 1)); // get the word_id
////    _word_id = _mm_cvtsi128_si32(_ids);
////            
////    return set_cached_address(vm, addr, _hash, word(_page, _word_id));
////    #undef _word_id
////    #undef _page
//}
//
//INLINE word_type *_translate_address_64_sse(struct virtual_memory_type *vm, word_type addr)
//{
//    register word_type
//        _hash asm("r8"),
//        _trans asm("r9");
//    
//    register void *_temp asm("r10");
//    
//    register __m128i
//        _cached_entry asm("xmm13"),
//        _ids asm ("xmm15"),
//        _masks asm ("xmm14") = _mm_set_epi64x(BLOCK_ID_MASK, PAGE_ID_MASK);
//
//    TRANSLATE_ADDRESS_SSE_64(
//        vm,
//        addr,
//        _trans,
//        _hash,
//        _temp,
//        _cached_entry,
//        _ids,
//        _masks
//    );
//    
//    return (word_type *)_trans;
////    _ids = _mm_and_si128(_ids, _masks);
////    // calculate page_id first.
////    _ids = _mm_srli_si128(_ids, (WORD_BIT_SIZE / 8));
////    _block = (void *)_mm_cvtsi128_si64(_ids); // get/save the page_id
////    
////    _ids = _mm_srli_si128(_ids, 8 + (PAGE_BIT_SIZE / 8)); // get the block
////    _block_id = _mm_cvtsi128_si64(_ids);
////
////    _ids = _mm_set1_epi64x((word_type)_block); // load back the page_id
////    
////    if (block_fault(vm, _block_id))
////    {
////        set_block(vm, _block_id, (_block = new_block()));
////        clear_block_fault(vm, _block_id);
////    }
////    else
////        _block = block(vm, _block_id);
////    
////    #define _page_id _block_id
////    _page_id = _mm_cvtsi128_si64(_ids);
////    if (page_fault((block_type *)_block, _page_id))
////    {
////        clear_page_fault((block_type *)_block, _page_id);
////        #define _page _block
////        _page = set_page((block_type *)_block, _page_id, new_page());
////    }
////    else
////        _page = page((block_type *)_block, _page_id);
////    #undef _page_id
////    
////    #define _word_id _block_id
////    _word_id = word_id(addr);
////
////    return set_cached_address(vm, addr, _hash, word(_page, _word_id));
////    #undef _word_id
////    #undef _page
//}


INLINE void move_word(struct virtual_memory_type *vm, word_type src_addr, word_type dest_addr)  {
    *translate_address(vm, dest_addr) = *translate_address(vm, src_addr);
}

INLINE void _set_word_(struct virtual_memory_type *mem, word_type address, word_type value) {
    set_word(mem, address, value);
}
INLINE word_type _get_word_(struct virtual_memory_type *mem, word_type address) {
    return get_word(mem, address);
}