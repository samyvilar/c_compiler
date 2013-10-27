#ifndef _BIT_HASH_H_
#define _BIT_HASH_H_

#include "word_type.h"

#define bit_hash_type unsigned int
#define ELEMENT_BIT_SIZE (BYTE_BIT_SIZE * sizeof(bit_hash_type))
// #define APPLICABLE_BITS_MASK (BITS_PER_ELEMENT - 1)

#define NUMBER_ELEMENTS(total) ((total / ELEMENT_BIT_SIZE) + (total % ELEMENT_BIT_SIZE))
#define bit(index) ((bit_hash_type)((bit_hash_type)1 << (bit_hash_type)index))

extern const bit_hash_type bit_masks[];
extern const bit_hash_type clear_bit_masks[];

#define element_index(index) ((index) / ELEMENT_BIT_SIZE)
#define bit_index(index) ((index) % ELEMENT_BIT_SIZE)

#define bit_mask(_index) bit(bit_index(_index)) // (bit_masks[bit_index(_index)]) // bit(bit_index) bit_masks[bit_index]
#define clear_bit_mask(_index) (~bit_mask(_index)) // (clear_bit_masks[bit_index(_index)]) // ((word_type)~bit_mask(bit_index)) // (clear_bit_masks[bit_index])

#define element(elements, index) (elements[element_index(index)])
#define bit_value(elements, index) (element(elements, index) & (bit_mask(index))) // (((bit_hash_type)1 << (bit_hash_type)max_bit_magnitude) - 1))))

#define set_bit_value(elements, index) (element(elements, index) |= (bit_mask(index)))
#define clear_bit_value(elements, index) (element(elements, index) &= (clear_bit_mask(index)))

#define set_all_bits(elements, number_of_elements) memset(elements, -1, NUMBER_ELEMENTS(number_of_elements) * sizeof(bit_hash_type))
#define clear_all_bits(elements, number_of_elements) memset(elements, 0, NUMBER_ELEMENTS(number_of_elements) * sizeof(bit_hash_type))

#endif
