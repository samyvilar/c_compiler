//
//  vm.h
//  virtual_machine
//
//  Created by Samy Vilar on 11/8/13.
//
//

#ifndef virtual_machine_vm_h
#define virtual_machine_vm_h

#include "word_type.h"
// 32 bit address space.
#define VM_NUMBER_OF_ADDRESSABLE_WORDS ((word_type)1 << 32)

word_type *allocate_entire_physical_address_space();

#endif
