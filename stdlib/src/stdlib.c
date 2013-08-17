

#include <stdlib.h>
#include <unistd.h>
#include <string.h>

typedef struct block_type
{
    struct block_type *next;
    size_t size;
} block_type;

#define size(block) (((block_type *)block)->size)
#define set_size(block, value) (size(block) = value)
#define next(block) (((block_type *)block)->next)
#define set_next(block, value) (next(block) = value)

void *initial_address = NULL;

#define PTR_SIZE sizeof(void *)
#define align(value) ((value + PTR_SIZE) - (value % PTR_SIZE))

#define NUMBER_OF_BLOCKS 256
block_type *freed_blocks[NUMBER_OF_BLOCKS];

static void _insert_block(block_type *block)
{
    block_type *blocks = freed_blocks[size(block)];
    if (block > blocks)    // blocks may be NULL, buts that's ok since all address are larger than NULL.
    {
        freed_blocks[size(block)] = block;
        set_next(block, blocks);
    }
    else
    {   // Search for a location in descending manner, until correct one or NULL is reached.
        while (next(blocks) > block)
            blocks = next(blocks);

        set_next(block, next(blocks));
        set_next(blocks, block);
    }
}


static void de_fragment()
{
    size_t block_size;
    int de_allocation = 1;
    block_type *blocks;

    while (de_allocation)
    {
        de_allocation = 0;
        for (block_size = 0; block_size < NUMBER_OF_BLOCKS; block_size++)
        {
            blocks = freed_blocks[block_size];
            while (blocks + block_size + sizeof(block_type) == sbrk(0))
            {
                brk(blocks);
                freed_blocks[block_size] = blocks = next(blocks);
                de_allocation = 1;
            }
        }
    }
}

/**
 * The goal of malloc is to allocate 'at least' number_of_bytes of contiguous memory in constant time, while
 * keeping fragmentation and slack as low as possible ...
 *
 */
void *malloc(size_t number_of_bytes)
{
    if (!initial_address)
        initial_address = sbrk(0);

    number_of_bytes = align(number_of_bytes);
    void *block;

    if (number_of_bytes < NUMBER_OF_BLOCKS && freed_blocks[number_of_bytes])
    {
        block = freed_blocks[number_of_bytes];
        freed_blocks[number_of_bytes] = next(block);
    }
    else
    {
        block = sbrk(number_of_bytes + sizeof(block_type));
        set_size(block, number_of_bytes);
    }

    set_next(block, block);  // Magic Number.
    return block + sizeof(block_type);
}

#define calloc(numb_elem, size_of_each) memset(malloc(numb_elem * size_of_each), 0, numb_elem * size_of_each)

#define get_block(address) (address - sizeof(block_type))
#define valid_address(address) (address && address > initial_address && address < sbrk(0) && next(get_block(address)) == get_block(address))

/**
 * The goal of free is to deallocate a previous allocated contiguous block of memory, unlike malloc which runs at constant
 * time, free doesn't since it tries de-fragment continuous set of memories, when ever possible, so it has linear time.
 *
 * The blocks will be order in increasing order so we can easily deallocate large chunks of continuous, once they are
 * the close enough to the heap pointer.
 */
void free(void *block)
{
    if (!valid_address(block))    // If invalid address just return ...
        return ;

    block -= sizeof(block_type);
    void *temp, *blocks;
    size_t alloc_size = sizeof(block_type) + size(block);

    if (block + alloc_size == sbrk(0))  // if it was the last block allocated just de-allocate it.
        brk(block);
    else if (size(block) < NUMBER_OF_BLOCKS)  // recycle block.
        _insert_block(block);
    else // block wasn't the last one and it exceeds largest cached block type, so break it up into different blocks
    {
        size_t
                current_size = size(block) + sizeof(block_type),
                bin_size = NUMBER_OF_BLOCKS;

        alloc_size = bin_size + sizeof(block_type);
        while (current_size > NUMBER_OF_BLOCKS + sizeof(block_type)) // break the block into the largest sequences of blocks.
        {
            temp = block;
            while ( (temp + alloc_size) <= (block + current_size - sizeof(block_type)) )  // while we can still insert 1 more contiguous into this bin
            {   // we can still hold 1 more sequential block.
                set_size(temp, bin_size);
                set_next(temp, (temp += alloc_size));
            }

            if (temp != block) // can we put any blocks in this bin
            {
                blocks = freed_blocks[bin_size];
                if (block > blocks) // does this sequence of blocks occur after the rest of the recycled blocks.
                {
                    freed_blocks[bin_size] = block;
                    set_next((temp - alloc_size), blocks);  // temp should hold the address of the last added block this sequence.
                }
                else
                {
                    while ((void *)next(blocks) > block) // look for the right position to insert this blocks.
                        blocks = next(blocks);
                    set_next((temp - alloc_size), next(blocks));
                    set_next(blocks, block);
                }
            }
            current_size -= temp - block;
            block = temp;

            bin_size -= PTR_SIZE;
            alloc_size -= PTR_SIZE;

            if (!bin_size || !alloc_size)
                break ;
        }

        bin_size = current_size - sizeof(block_type);
        blocks = freed_blocks[bin_size];
        if (block > blocks)
        {
            freed_blocks[bin_size] = block;
            set_next(block, blocks);
        }
        else
        {
            while ((void *)next(blocks) > block)
                blocks = next(blocks);
            set_next(block, next(blocks));
            set_next(next(blocks), block);
        }
        set_size(block, bin_size);
    }
    de_fragment(); // de-fragment memory.
}

#undef size
#undef set_size
#undef next
#undef set_next

#undef get_block
#undef valid_address
#undef align
