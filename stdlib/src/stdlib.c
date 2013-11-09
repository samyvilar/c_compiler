

#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <stdio.h>

typedef struct block_type
{
    struct block_type *next;
    size_t size;
} block_type;

#define size(block) (((block_type *)block)->size)
#define set_size(block, value) (size(block) = value)
#define next(block) (((block_type *)block)->next)
#define set_next(block, value) (next(block) = value)

#define invalidate_block(block) set_next(block, NULL)
#define validate_block(block) set_next(block, block)
#define is_block_invalid(init_address) ((init_address <= __base_heap_ptr__) \
    || (init_address > __heap_ptr__)  \
    || (next(get_block(init_address)) != get_block(init_address)))

#define NUMBER_OF_BLOCKS 256
#define MINIMUM_BLOCK_SIZE (sizeof(block_type)) // it has to be a multiple of block_type or else free won't properly work
#define bin_id(size) (size / MINIMUM_BLOCK_SIZE) // since all blocks are a multiple of MINIMUM_BLOCK_SIZE
#define bin_size(_id) (_id * MINIMUM_BLOCK_SIZE)

block_type *freed_blocks[NUMBER_OF_BLOCKS];


static void _insert_block(block_type *block)
{
    int bin = bin_id(size(block));
    block_type *blocks = freed_blocks[bin];

    if (block > blocks)    // blocks may be NULL, buts that's ok since all address are larger than NULL.
    {
        set_next(block, blocks);  // save the rest of the blocks ...
        freed_blocks[bin] = block; // add this block to the link list ...
    }
    else
    {   // Search for a location in descending manner, until correct one or NULL is reached.
        while (next(blocks) > block)
            blocks = next(blocks);

        set_next(block, next(blocks)); // save the rest of the blocks ...
        set_next(blocks, block); // insert this block ...
    }
}


static void de_fragment()
{
    int
        de_allocation = 1,
        bin;

    void *blocks;

    while (de_allocation)
    {
        de_allocation = 0;
        bin = NUMBER_OF_BLOCKS; // start with the largest bin ...

        while (bin--)  // go through all the bins from largest to smallest ...
        {
            blocks = freed_blocks[bin];
            while ((blocks + bin_size(bin) + sizeof(block_type)) == sbrk(0))
            {
                brk(blocks); // deallocate block ...
                freed_blocks[bin] = blocks = next(blocks); // remove block from list ...
                de_allocation = 1; // go through the list 1 more time ... and check next block...
            }
        }
    }
}

/**
 * The goal of malloc is to allocate 'at least' number_of_bytes of contiguous memory in constant time, while
 * keeping fragmentation and slack as low as possible ...
 **/
void *malloc(size_t number_of_bytes)
{
    void *block;
    number_of_bytes += (MINIMUM_BLOCK_SIZE - (number_of_bytes % MINIMUM_BLOCK_SIZE)); // align
    int bin = bin_id(number_of_bytes); // calculate bin index ...

    if (bin < NUMBER_OF_BLOCKS && freed_blocks[bin])
    {
        block = freed_blocks[bin];       // get a previously recycled block ...
        freed_blocks[bin] = next(block); // remove it from the list ...
    }
    else // either we don't have any recycled blocks or it exceeds the max size ... TODO: see if we can merge blocks ...
    {
        block = sbrk(number_of_bytes + sizeof(block_type));
        set_size(block, number_of_bytes);
    }

    validate_block(block);  // Magic Number.
    return block + sizeof(block_type);
}

#define calloc(numb_elem, size_of_each) memset(malloc(numb_elem * size_of_each), 0, numb_elem * size_of_each)

#define get_block(address) ((void *)address - sizeof(block_type))
// the address cannot equal the __base_heap_ptr__ since we are incrementing by sizeof(block_type)
// regardless of allocation size ...
// but may equal the __heap_ptr__ if it was the last allocation with zero size ...

/**
 * The goal of free is to deallocate a previous allocated contiguous block of memory, unlike malloc which runs at constant
 * time, free doesn't since it tries de-fragment continuous set of memories, when ever possible, so it has linear time.
 *
 * The blocks will be ordered in an ascending manner, so we can easily deallocate large chunks of continuous,
 * once they are the close enough to the heap pointer.
 */
void free(void *block)
{
    if (is_block_invalid(block))    // If invalid address just return ...
        return ;

    block = get_block(block);  // get block_type object (ptr-to-next-block, size, ...)

    size_t alloc_size = size(block); // get allocation size excluding required info for block  ...
    set_next(block, NULL);  // invalidate block ... in case its ever freed again ...

    if ((block + alloc_size + sizeof(block_type)) == sbrk(0))  // if it was the last block allocated just de-allocate it.
        brk(block);
    else if (bin_id(alloc_size) < NUMBER_OF_BLOCKS)  // recycle block.
        _insert_block(block);
    else
    /* block wasn't the last one and it exceeds largest cached block type, so break it up into different continuous blocks
     * assuming that all sizes are a multiple of sizeof(block_type) ...
     */
    {
        long long int
            remaining_bytes = alloc_size + sizeof(block_type),
            bin = NUMBER_OF_BLOCKS - 1; // start with the largest bin ...

        void *end_of_block = block + remaining_bytes;

        alloc_size = bin_size(bin);  // bin_id is proportional to the MINIMUM_BLOCK_SIZE

        void *temp, *blocks;

        // break the block into a set of largest sequences of blocks, until none remain ...
        while (remaining_bytes)
        {
            temp = block;
            // while creating an extra continuous block doesn't exceed the remaining bytes ...
            while ( (temp + alloc_size + sizeof(block_type)) <= end_of_block)
            {   // we can still hold 1 more sequential block.
                set_size(temp, alloc_size);
                set_next(temp, (temp += (alloc_size + sizeof(block_type)))); // create/remove/add link to next 'possible' block ...
            }

            if (temp != block) // did we create any blocks, if so insert them ...
            {
                blocks = freed_blocks[bin];
                if (block > blocks) // does this sequence of blocks occur after the rest of the recycled blocks.
                {
                    // temp should be the address to the next 'possible' block, get last added block ...
                    set_next((temp - alloc_size - sizeof(block_type)), blocks); // save the rest of the recycled blocks
                    freed_blocks[bin] = block; // add this sequence of blocks ...
                }
                else
                {
                    while (next(blocks) > block) // look for the first next block that lies before this sequence
                        blocks = next(blocks);

                    set_next((temp - alloc_size - sizeof(block_type)), next(blocks)); // save the rest
                    set_next(blocks, block); // add this sequence
                }
                // remove this sequence of blocks ...
                remaining_bytes -= (temp - block);
                block = temp;
            }

            if (bin)
            {
                bin--;
                alloc_size -= MINIMUM_BLOCK_SIZE;
            }
            else // bin_size must be zero ... so reset it
            {
                bin = NUMBER_OF_BLOCKS - 1;
                alloc_size = bin_size(bin);
            }
        }
    }
    de_fragment(); // de-fragment memory. TODO: this is quite expenssive see if we can do this once everywhile not every time ...
}


unsigned long int next = 1;
int rand()  {
    return (unsigned int)( (next = ((next * 1103515245) % (1 << (sizeof(int) - 1) * 8) + 12345)) / 65536 ) % 32768;
}

void srand(unsigned int seed) {
    next = seed;
}