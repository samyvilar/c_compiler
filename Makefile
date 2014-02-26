.PHONY: all test clean stdlib vm

all: vm stdlib

stdlib:
		./cc.py -a stdlib/src/unistd.c stdlib/src/stdlib.c stdlib/src/string.c stdlib/src/stdio.c -o stdlib/libs/libc.p

test:
		nosetests

vm:
		$(MAKE) -C back_end/virtual_machine/c all
clean:
		rm -f stdlib/libs/libc.p
		$(MAKE) -C back_end/virtual_machine/c clean

