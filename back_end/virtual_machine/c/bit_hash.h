#ifndef _BIT_HASH_H_
#define _BIT_HASH_H_

#include <stdlib.h>

#define bit_hash_type unsigned long long int

#define NUMBER_ELEMENTS(total) (total/(8*sizeof(bit_hash_type)))
#define bit(index) ((bit_hash_type)1 << (bit_hash_type)index)

extern const bit_hash_type bit_masks[];
#define bit_mask(bit_index) (bit_masks[bit_index]) // bit(bit_index) bit_masks[bit_index] // (1 << (bit_index))

#define element(elements, index) (elements[((index)/(8 * sizeof(bit_hash_type)))])
#define bit_value(elements, index) (element(elements, index) & (bit_mask((index) % (8 * sizeof(bit_hash_type)))))

#define set_bit_value(elements, index) (element(elements, index) |= bit_mask((index) % (8 * sizeof(bit_hash_type))))
#define clear_bit_value(elements, index) (element(elements, index) &= ~bit_mask((index) % (8 * sizeof(bit_hash_type))))

#define set_all_bits(elements, number_of_elements) memset(elements, -1, number_of_elements/sizeof(bit_hash_type))
#define clear_all_bits(elements, number_of_elements) memset(elements, 0, number_of_elements/sizeof(bit_hash_type))

#endif