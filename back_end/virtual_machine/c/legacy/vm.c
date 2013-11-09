//
//  vm.c
//  virtual_machine
//
//  Created by Samy Vilar on 11/8/13.
//
//

#include <stdlib.h>
#include <sys/mman.h>
#include "vm.h"
#include "word_type.h"

const word_type vm_number_of_addressable_words = VM_NUMBER_OF_ADDRESSABLE_WORDS;

word_type *allocate_entire_physical_address_space(){
    return mmap(
        NULL,
        VM_NUMBER_OF_ADDRESSABLE_WORDS * sizeof(word_type),
        PROT_READ | PROT_WRITE, MAP_ANON | MAP_SHARED,
        0,
        0
    );
}
