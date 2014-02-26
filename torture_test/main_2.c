//
//  main.c
//  adv_data_structures_zero_credit_report
//
//  Created by Samy Vilar on 11/19/12.
//  Copyright (c) 2012 __MyCompanyName__. All rights reserved.
//

#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <string.h>

#define TRACK_STATISTICS
//#define SEED_RANDOM_NUMBER_GENERATOR

/* There is a slight performance boost when working with words.  */
#if __GNUC__
    #if __x86_64__ || __ppc64__ /* check that we are on a 64 bit machine. */
        typedef unsigned long long word_type; /* use 64 bit words. */
        /* prime number that can be stored using 32 bits, unsigned. for signed you can use 2147483647. */
        #define MAX_PRIME 4294967291

    #else
        typedef unsigned int word_type;
    #endif
#else /* if we are not using gcc just stick with unsigned int, note we can still use 64 bit ints though they are quite slower on 32 bit machines. */
    typedef unsigned int word_type;
    /* prime number that can be stored using 16 bits, unsigned. for signed you can use 32749. */
    #define MAX_PRIME 65521
#endif
/* work with unsigned characters since we are working with unsigned words, mixing signs affects performance. */
typedef unsigned char char_type;
const word_type number_of_bits_per_word = (sizeof(word_type) * 8);


/* masks to update bit
 * use bitwise or operator to set it to 1,
 * use bitwise and operator to get a single bit.
 * setting the bit to 0 would require inverting
 * the mask and applying the bitwise and operator not needed here ... */
static word_type masks[(sizeof(word_type) * 8)] = {0};

/* Set of macros to allow us to work with individual bits from our field. */

/* get the location of the word which holds the ith bit  */
#define word_index(index) (index/number_of_bits_per_word)

/* get the location of the ith bit withing a word. */
#define bit_index(index) (index % number_of_bits_per_word)

/* get a word from our bit field */
#define word(bit_field, index) (bit_field[word_index(index)])

/* get bit, either returns 0 if its zero or its current value depending on its location in the word, (1, 2, 4, 8 ...)*/
#define get_bit(bit_field, index) (word(bit_field, index) & masks[bit_index(index)])

/* set bit at index within our bit field to 1. */
#define set_bit_to_1(bit_field, index) (bit_field[word_index(index)] |= masks[bit_index(index)])

/* Initialize our masks ... */
void initialize_masks()
{
    word_type index = number_of_bits_per_word;
    while (index--)
        masks[index] = (word_type)1 << index; /* set each bit by shifting 1 to the right, accordingly. */
}


/* Link list of hash function parameters,
 * the first contains the table size,
 * the second is coefficient_b and
 * the third and on wards hold values of coefficient_a.
 * As always the list terminates with NULL.
 */
typedef struct hash_function_parameters_type
{
    struct hash_function_parameters_type
            *coefficients;

    word_type
            value;

} hash_function_parameters_type;

/* some micros to control the way we deal with this structure.  */
#define next_parameter(hash_func_parameter) (*(hash_function_parameters_type **)hash_func_parameter)
#define set_next_parameter(hash_func_parameter, next_param) (next_parameter(hash_func_parameter) = next_param)
#define value(hash_func_parameter) (hash_func_parameter->value)
#define set_value(hash_func_parameter, param_value) (value(hash_func_parameter) = param_value)
#define set_coefficient_a set_value
#define table_size(hash_func_parameter) value(hash_func_parameter)
#define set_table_size set_value
#define coefficient_b(hash_func_parameter) value(next_parameter(hash_func_parameter))
#define set_coefficient_b(hash_func_parameter, coefficient) (coefficient_b(hash_func_parameter) = coefficient)
#define coefficient_a value
#define initial_coefficient_a(hash_func_parameter) next_parameter(next_parameter(hash_func_parameter))

/* the size of the allocation block use higher values if expecting to hash very long strings... */
#define ALLOCATION_BLOCK_SIZE 128

/* A pre-allocated blocks of parameters used for the hash function. */
static hash_function_parameters_type
        *allocated_block = NULL,
        *max_block       = NULL; /* address of last element withing our block. */

/* return a single hash_func_parameter object with all fields zero out, allocates new block if exhausted. */
hash_function_parameters_type *allocate_node()
{
    if (allocated_block == max_block)   /* if we don't have any pre-allocated nodes left, or initially empty, allocate nodes. */
    {
        max_block = malloc(sizeof(hash_function_parameters_type) * ALLOCATION_BLOCK_SIZE + sizeof(void *));
        *(hash_function_parameters_type **)&max_block[ALLOCATION_BLOCK_SIZE] = allocated_block; /* save previous block. */
        allocated_block = max_block; /* set new block. */
        max_block = allocated_block + ALLOCATION_BLOCK_SIZE; /* locate last unavailable node */
        memset(allocated_block, 0, sizeof(hash_function_parameters_type) * ALLOCATION_BLOCK_SIZE); /* zero out the whole block,
                        also move pages from vm pool into main memory, if not present. */
    }

    return allocated_block++; /* return current address, increment for next item. */
}

/* Family of Universal hashing function, for null terminated strings
 * it takes in a link list of parameters, where
 * the first is the table size
 * the second is coefficient_b randomly chosen from [0, RAND()]
 * and the third and onward are coefficient_a each randomly chosen from [0, RAND()]
 * where RAND() returns a value from  [0, RAND_MAX]
 * RAND_MAX is system dependent, if integer is 32 bits it should 2147483647 or 0x7fffffff largest positive integer.
 * all have to be less than MAX_PRIME.
 * note that we need as many coefficient_a as the length of the string
 * shorter strings simply are interpret as being padded by 0s so the hash values aren't affected when we increment the list.
 *
 * The function using python notation.
 * hash(string) = (sum( (char_value * coefficient_as[index]) % MAX_PRIME
 *                          for index, char_value in enumerate(string)
 *                    ) + coefficient_b) % table_size
 */
word_type universal_hash_function(char_type *char_value, hash_function_parameters_type *hash_func_parameter)
{
    word_type max_value = table_size(hash_func_parameter),
              sum       = coefficient_b(hash_func_parameter);

    hash_func_parameter = initial_coefficient_a(hash_func_parameter);
    char_value--; /* subtract the pointer by one so every time we begin at the loop we just need increment and check it */
                  /* note that ++ is applied on the pointer. */
    while (*++char_value) /* while we haven't read the null character, '\0'. */
    {
        if (!next_parameter(hash_func_parameter)) /* if we need a new coefficient_a add it */
        {
            set_next_parameter(hash_func_parameter, allocate_node());
            set_coefficient_a(next_parameter(hash_func_parameter), (((word_type)rand()) % MAX_PRIME));
        }
        sum += (coefficient_a(hash_func_parameter) * ((word_type) *char_value)) % MAX_PRIME;

        hash_func_parameter = next_parameter(hash_func_parameter); /* move to next parameter. */
    }

    return (sum % max_value);
}

/* A structure use to check whether or not a giving string is withing our set. */
typedef struct membership_type
{
    word_type
        *bit_field,     /* a bit field used to hold whether or not an element is present, if the bit 1 its present otherwise it isn't. */
        number_of_bits, /* the size of the bit field it cannot exceed MAX_PRIME! */
        (*hashing_function)(char_type *, hash_function_parameters_type *); /* the hashing function use to determine
                                                                             the hash or index of value withing our bit field */
    hash_function_parameters_type
        *hashing_function_parameters; /* link list of parameters to be used by the hashing function. */

    #ifdef TRACK_STATISTICS
        /* the following properties will be used by insert and find to keep track of members and collisions */
        word_type
            number_of_set_bits,         /* this will keep track of the number of inserts assuming that each is unique, counting bits can be quite expensive */
            number_of_inserts,          /* keeps track of the number items that where inserted, assuming, that each is unique, the diff between it and set_bits is the number of collisions */
            number_of_false_positives,  /* this will keep track of words are in the member but never inserted. */
            number_of_false_negatives;  /* this represents the number of words that weren't found but had being inserted, this should be zero!. */
    #endif

} membership_type;

/* some micros to work with this structure. */
#define bit_field(membership) (*(word_type **)membership)
#define set_bit_field(membership, bitfield) (bit_field(membership) = bitfield)
#define number_of_bits(membership) membership->number_of_bits
#define set_number_of_bits(membership, value) (number_of_bits(membership) = value)
#define hashing_function(membership) membership->hashing_function
#define set_hashing_function(membership, function) (hashing_function(membership) = function)
#define hashing_func_parameters(membership) membership->hashing_function_parameters
#define set_hashing_func_parameters(membership, param) (hashing_func_parameters(membership) = param)

void error(char message[])
{
    printf("Error: %s\n", message);
    exit(-1);
}

/* Creates a membership structure with a bitfield containing at least 'size' bits. */
membership_type *create_membership(word_type size)
{
    if (size >= MAX_PRIME)
        error("The bit field cannot be created with size larger then MAX_PRIME!");

    if (!masks[0]) /* if we haven't initialized our masks initialize them. */
        initialize_masks();

    membership_type *membership = calloc(1, sizeof(membership_type)); /* zero out all fields ... */

    set_number_of_bits(membership, size);
    set_hashing_function(membership, universal_hash_function);

    set_hashing_func_parameters(membership, allocate_node()); /* initial node to hold table_size */
    set_next_parameter(hashing_func_parameters(membership), allocate_node()); /* second node to hold coefficient b*/
    set_next_parameter(next_parameter(hashing_func_parameters(membership)), allocate_node()); /* third node for coefficient a */

    /* seed the random number generator, note if seeded by time hashes will differ at every run ... */
    #ifdef SEED_RANDOM_NUMBER_GENERATOR
        srand((unsigned int)time(NULL));
    #endif

    set_table_size(hashing_func_parameters(membership), size); /* set coefficient the table size */
    set_coefficient_b(hashing_func_parameters(membership), (rand() % MAX_PRIME)); /* set coefficient b */
    set_value(next_parameter(next_parameter(hashing_func_parameters(membership))), (rand() % MAX_PRIME)); /* set coefficient a */

    size = ((size/number_of_bits_per_word) + 1); /* calculate number bytes required to allocate bit field. */

    set_bit_field(membership, calloc(size, sizeof(word_type)));

    return membership;
}

void free_membership(membership_type *membership)
{
    free(bit_field(membership));
    free(membership);
}


void insert_string(membership_type *membership, char *value)
{
    char_type *string = (char_type *)value;
    word_type hash = hashing_function(membership)(string, hashing_func_parameters(membership));

    #ifdef TRACK_STATISTICS
        membership->number_of_inserts++;            /* increase insert count. */

        if (get_bit(bit_field(membership), hash))   /* if the bit has already being set, just return. */
            return ;

        set_bit_to_1(bit_field(membership), hash);  /* set bit to 1 */
        membership->number_of_set_bits++;           /* increase number of bits set. */
    #else
        /* if we are tracking any statistics just set the bit to 1. */
        set_bit_to_1(bit_field(membership), hash);  /* set bit to 1 */
    #endif
}

/* if the string is not a member return 0 otherwise return a non-zero if it is a member,
 * the non-zero value return has no meaning!
 */
word_type is_member(membership_type *membership, char *value, word_type is_present)
{
    char_type *string = (char_type *)value;
    word_type hash = hashing_function(membership)(string, hashing_func_parameters(membership));

    /* if we are not tracking statistics just return the bit value, if present its value will be non-zero, if 0 its not present. */
    #ifndef TRACK_STATISTICS
        return get_bit(bit_field(membership), hash); /* return the actual bit which is 0 or 1,2,4,8, .... */
    #else
        if (get_bit(bit_field(membership), hash)) /* we got a hit. */
        {
            if (!is_present)  /* but we weren't expecting it. */
                membership->number_of_false_positives++; /* increase count and return 1 */
            return 1;
        }
        if (is_present)
        {
            membership->number_of_false_negatives++;
            printf("WARNING!! false negative '%s'\n", string);
        }
        return 0;
    #endif
}

/* return a list of string each unique created
 * by going over all the possible combinations of the giving alphabet,
 * with the first string being the empty or null string
 * note: it assumes all symbols are unique.
 */
char **get_combinations(word_type number_of_words, char *alphabet)
{
    if (!alphabet || !number_of_words || !*alphabet) /* if alphabet is NULL or number_of_words is zero or  */
        return NULL;                                 /* the first value of the alphabet is 0 just return NULL */

    char
            **string = malloc(sizeof(char *) * number_of_words + 1), /* set of all strings plus the empty string. */
            **current_string = string, /* the current string we are working with/ */
            **final_string = (string + number_of_words + 1),   /* the final string. */
            *alphabet_index,
            *prefix;

    *current_string++ = calloc(1, sizeof(char)); /* set the current initial string to the empty string, and increment to the next. */

    word_type
            current_size_of_string,     /* the number of bytes required to hold the current combination  */
            current_prefix_length  = 0, /* the length of the current prefix */
            stack_index            = 0; /* stack index, the empty string has being already being pushed. */

    while (current_string < final_string)  /* while we are not at the last string ... */
    {
        alphabet_index = alphabet;        /* reset alphabet to initial symbol. */
        prefix = string[stack_index++];   /* pop an element from the stack */
        current_prefix_length = strlen(prefix); /* calc the length of the current prefix  */
        current_size_of_string = current_prefix_length + 2; /* add 2 bytes one for the symbol and the other the null value. */

        /* add all the possible combinations of the current element
            pushing them on to the stack. */

        while ((current_string < final_string) && *alphabet_index)
        {
            *current_string = calloc(current_size_of_string, sizeof(char)); /* allocate memory for new combination, zero out */
            memcpy(*current_string, prefix, current_prefix_length); /* copy prefix */
            (*current_string++)[current_prefix_length] = *alphabet_index++;
        }
    }

    return string;
}

word_type factorial(word_type value)
{
    word_type sum = value;
    while (--value)
        sum *= value;
    return sum;

}

/* permute a giving string number_of_permutations times,  */
char **permute_string(char *str, word_type number_of_permutations)
{
    if (!str || !number_of_permutations || (number_of_permutations > factorial(strlen(str))))
        return NULL;

    word_type
            loc,
            index_0,
            index_1,
            length = strlen(str),
            temp_loc;

    char
        **permutations = malloc(sizeof(char *) * number_of_permutations),
        **current_permutation = permutations,
        *original_string = calloc(length + 1, sizeof(char)),
        *string = calloc(length + 1, sizeof(char)),
        temp;

    memcpy(original_string, str, length);
    memcpy(string, str, length);

    for (index_0 = 0; index_0 < number_of_permutations; index_0++)
    {
        temp_loc = index_0;
        memcpy(string, original_string, length);
        for (index_1 = 1; index_1 < length; ++index_1)
        {
            loc = (index_0 % (index_1 + 1));
            temp = string[loc];
            string[loc] = string[index_1];
            string[index_1] = temp;
            index_0 = (index_0 / (index_1 + 1));
        }
        index_0 = temp_loc;
        *current_permutation = calloc(length + 1, sizeof(char));
        memcpy(*current_permutation, string, length);
        current_permutation++;
    }

    return permutations;
}


void do_statistical_tests()
{
    #ifndef TRACK_STATISTICS
        printf("Enable TRACK_STATISTICS to do statistical tests...\n");
        return ;
    #else
    /* some sizes test to see how the bitfield or rather hashing function behaves depending on its size. */
    unsigned int
            sizes_to_test[]     = {10000,   /* 10 thousands bits, about 1.25 kilobytes. */
                                   100000,  /* 12.5 kilobytes. */
                                   1000000, /* 125 kilobytes   */
                                   10000000 /* 1.25 megabytes. */},
             number_of_sizes    = 4,
             index_0, index_1,
             number_of_strings  = 10000;

    /* create two set of strings both of which are completely disjoint (if the empty string is excluded),
        in principles their shouldn't be any collisions.
    */
    char **inserted_strings     = get_combinations(number_of_strings, "abcdefghi"),
         **non_inserted_strings = get_combinations(number_of_strings, "jklmnopqr");

    printf("Testing with combinations.\n");
    membership_type *membership;
    for (index_0 = 0; index_0 < number_of_sizes; index_0++)
    {
        membership = create_membership(sizes_to_test[index_0]); /* create a new membership. */
        for (index_1 = 1; index_1 <= number_of_strings; index_1++) /* skip over the empty string */
            insert_string(membership, inserted_strings[index_1]);
        for (index_1 = 1; index_1 <= number_of_strings; index_1++) /* skip over the empty string */
            if (!is_member(membership, inserted_strings[index_1], 1))
                error("Failed to insert value!");
        for (index_1 = 1; index_1 <= number_of_strings; index_1++)
            is_member(membership, non_inserted_strings[index_1], 0);

        printf("Bitfield size %u number_of_strings %u\n", sizes_to_test[index_0], number_of_strings);

        printf("%u, %3.2f%% collisions while inserting.\n",
                (unsigned int)(number_of_strings - membership->number_of_set_bits),
                (((unsigned int)(number_of_strings - membership->number_of_set_bits)/(double)(number_of_strings)) * 100));

        printf("%u, %3.2f%% collisions while searching.\n",
                (unsigned int)(membership->number_of_false_positives),
                (((unsigned int)(membership->number_of_false_positives)/(double)(number_of_strings)) * 100) );
        printf("\n");

        free_membership(membership);
    }

    for (index_0 = 0; index_0 < number_of_strings + 1; index_0++)
    {
        free(inserted_strings[index_0]);
        free(non_inserted_strings[index_0]);
    }

    printf("Testing with permutations.\n");
    inserted_strings = permute_string("abcdefghi", number_of_strings);
    non_inserted_strings = permute_string("jklmnopqr", number_of_strings);
    for (index_0 = 0; index_0 < number_of_sizes; index_0++)
    {
        membership = create_membership(sizes_to_test[index_0]); /* create a new membership. */
        for (index_1 = 0; index_1 < number_of_strings; index_1++)
                insert_string(membership, inserted_strings[index_1]);
        for (index_1 = 0; index_1 < number_of_strings; index_1++)
                if (!is_member(membership, inserted_strings[index_1], 1))
                    error("Failed to insert value!");
        for (index_1 = 0; index_1 < number_of_strings; index_1++)
            is_member(membership, non_inserted_strings[index_1], 0);

        printf("Bitfield size %u number_of_strings %u\n", sizes_to_test[index_0], number_of_strings);

        printf("%u, %3.2f%% collisions while inserting.\n",
                (unsigned int)(number_of_strings - membership->number_of_set_bits),
                (((unsigned int)(number_of_strings - membership->number_of_set_bits)/(double)(number_of_strings)) * 100));

        printf("%u, %3.2f%% collisions while searching.\n",
                (unsigned int)(membership->number_of_false_positives),
                (((unsigned int)(membership->number_of_false_positives)/(double)(number_of_strings)) * 100) );
        printf("\n");

        free_membership(membership);
    }

    for (index_0 = 0; index_0 < number_of_strings; index_0++)
    {
        free(inserted_strings[index_0]);
        free(non_inserted_strings[index_0]);
    }

    #endif
}


void do_benchmark()
{
    word_type total = 10000000,
              temp = total;

    char **strings = permute_string("kjlasdfjh02h3rpogasepgb", total);

    double start_time, end_time;

    membership_type *membership = create_membership(total * 10);
    start_time = ((double)clock())/CLOCKS_PER_SEC;
    while (temp--)
        insert_string(membership, strings[temp]);
    end_time = ((double)clock())/CLOCKS_PER_SEC;

    printf("Inserted %u in %.2f seconds at an avg of %.2f/s\n",
            (unsigned int)total,
            (end_time - start_time),
            (unsigned int)total/(end_time - start_time));

    temp = total;
    start_time = ((double)clock())/CLOCKS_PER_SEC;
    while (temp--)
        is_member(membership, strings[temp], 1);
    end_time = ((double)clock())/CLOCKS_PER_SEC;

    printf("Queried %u elements in %.2fs at an avg of %.2f/s\n",
            (unsigned int)total,
            (end_time - start_time),
            (unsigned int)total/(end_time - start_time));



}


int main (int argc, const char * argv[])
{
    do_statistical_tests();
    do_benchmark();

    return 0;
}
