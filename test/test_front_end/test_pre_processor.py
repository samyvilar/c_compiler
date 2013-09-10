__author__ = 'samyvilar'

from unittest import TestCase
from front_end.loader.load import source
from front_end.tokenizer.tokenize import tokenize
from front_end.preprocessor.preprocess import preprocess


class TestPreProcessor(TestCase):
    def test_pre_processor(self):
        code = """
            #define a 1
            #define b(a) a

            #if defined(b) - 1 + defined a
            b(a)
            #else
            1
            #endif
        """
        for token in preprocess(tokenize(source(code))):
            self.assertEqual(token, '1')

    def test_stringification(self):
        code = """
        #define foo(e) #e
        foo(hello)
        """
        for token in preprocess(tokenize(source(code))):
            self.assertEqual(token, 'hello')

    def test_token_concatenation(self):
        code = """
        #define foo(a, b) a ## b  ## 5 ## #a
        foo("h", "ello")
        """
        for token in preprocess(tokenize(source(code))):
            self.assertEqual(token, 'hello5h')

    def test_nested_obj_macros(self):
        code = """
            #define is_aligned(address, size) (!(((unsigned long)address) & (size - 1)))
            #define vector_type void *
            is_aligned((dest + numb - sizeof(vector_type)), sizeof(vector_type))
        """
        self.assertEqual(
            '( ! ( ( ( unsigned long ) ( dest + numb - sizeof ( void * ) ) ) & ( sizeof ( void * ) - 1 ) ) )',
            ' '.join(preprocess(tokenize(source(code)))),
        )

    def test_nested_func_macros(self):
        code = """
            #define size(block) (((block_type *)block)->size)
            block_type *blocks = freed_blocks[size(block)];
        """
        self.assertEqual(
            'block_type * blocks = freed_blocks [ ( ( ( block_type * ) block ) -> size ) ] ;',
            ' '.join(preprocess(tokenize(source(code))))
        )

    def test_multiple_nested_func_macros(self):
        code = """
            #define size(block) (((block_type *)block)->size)
            #define set_size(block, value) (size(block) = value)
            #define next(block) (((block_type *)block)->next)
            #define set_next(block, value) (next(block) = value)

            set_next(next(blocks), block);
        """
        self.assertEqual(
            '( ( ( ( block_type * ) ( ( ( block_type * ) blocks ) -> next ) ) -> next ) = block ) ;',
            ' '.join(preprocess(tokenize(source(code))))
        )

    def test_bug(self):
        code = """
        #define vector_type void *
        #define __copy_element__(src, dest, element_type, index) (*(element_type *)(dest + index) = *(element_type *)(src + index))
        __copy_element__(src, dest, vector_type, index);
        """
        self.assertEqual('( * ( void * * ) ( dest + index ) = * ( void * * ) ( src + index ) ) ;',
                         ' '.join(preprocess(tokenize(source(code)))))

    def test_bug_1(self):
        code = """
        #define LEFT_NODE(tree) tree->left
        #define VALUE LEFT_NODE
        VALUE(VALUE(old_leaf)) = old_leaf;
        """
        self.assertEqual('old_leaf -> left -> left = old_leaf ;', ' '.join(preprocess(tokenize(source(code)))))