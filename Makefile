.PHONY: all test clean stdlib vm

all: stdlib vm

stdlib:
		./c_comp.py -a stdlib/src/unistd.c stdlib/src/stdlib.c stdlib/src/string.c stdlib/src/stdio.c -o stdlib/libs/libc.p

test:
		nosetests

vm:
		$(MAKE) -C back_end/virtual_machine/c all
clean:
		rm stdlib/libs/libc.p

