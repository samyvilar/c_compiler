//
//  main.c
//  adv_data_structures_hw_3
//
//  Created by Samy Vilar on 11/16/12.
//  Copyright (c) 2012 __MyCompanyName__. All rights reserved.
//

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* ENABLES CHECKS on all public functions. */
// #define SAFE_MODE

/*
    Represents an ordered set, created with two trees
     one tree holds the keys to identify each value
     and the second tree holds the order of each value
     the trees are connected via their leaves.

     Both trees are self-balanced on height.

    Convention:
        Both trees:
            if tree->left == NULL is an empty tree
            if tree->RIGHT == NULL and tree->left != NULL its a leave.
                tree->left holds address of value, in this case pointer to either its 'ordered' or 'key' leaf.
            if tree->left != NULL and tree->right != NULL is a complete tree.
            if tree->parent == NULL then it must be the root.

        Key Tree:
            tree->left->key < tree->key
 */

typedef unsigned int key_type;       /* type of key used to identify each value withing our set, it must support comparisons. */
typedef struct ordered_set_tree_node_type
{
    struct ordered_set_tree_node_type
            *right,      /* right child, declared first, we only need to dereference to use it. */
            *left,       /* left child */
            *parent;     /* parent of this node or NULL if at root node. */

    key_type
            key;         /* key of this node used for querying when working with Key Tree */

    unsigned int
            height;      /* height of this node, used for re-balancing. */

} ordered_set_tree_node_type;

/* Since we are assuming an order on struct we should use macros in case the order changes. */
#define RIGHT_NODE(tree) (*(ordered_set_tree_node_type**)tree)
#define IS_TREE RIGHT_NODE
#define IS_EMPTY_TREE !LEFT_NODE
#define LEFT_NODE(tree) tree->left
#define PARENT_NODE(tree) tree->parent
#define KEY(tree) tree->key
#define VALUE LEFT_NODE
#define HEIGHT(tree) tree->height

#define NODE_BLOCK_SIZE 511                 /* The number of nodes to preallocate at each block, make sure its
                                               high for large trees */
ordered_set_tree_node_type
        *allocated_nodes_block    = NULL,   /* represents a block of nodes pre-allocated */
        *recycled_nodes_link_list = NULL;   /* represents a link list of recycled nodes  */
unsigned int
        number_of_allocated_nodes = 0;      /* represents the number of allocated nodes ready to be used. */

/* recycle node for later use */
void recycle_node(ordered_set_tree_node_type *);
void recycle_node(ordered_set_tree_node_type *tree)
{
    RIGHT_NODE(tree) = recycled_nodes_link_list; /* set the right node to the previously recycled nodes. */
    recycled_nodes_link_list = tree;             /* recycle this node making it the first accessible one.  */
}

/* allocate a new node, either from recycled or pre-allocated block. */
ordered_set_tree_node_type *allocate_node();
ordered_set_tree_node_type *allocate_node()
{
    ordered_set_tree_node_type *tree;

    if (!number_of_allocated_nodes) /* if we don't have any pre-allocated nodes, allocate a block just in case. */
    {                                                                         /* allocate block plus a few bytes for                                                                                  address to previous block. */
        tree = malloc((sizeof(ordered_set_tree_node_type) * NODE_BLOCK_SIZE) + sizeof(ordered_set_tree_node_type *));
        number_of_allocated_nodes = NODE_BLOCK_SIZE;
        *(ordered_set_tree_node_type **)(&tree[NODE_BLOCK_SIZE]) = allocated_nodes_block; /* link previous block to current block. */
        allocated_nodes_block = tree;
    }   /* we can only deallocate all blocks!, de-allocating single blocks would require a diff mem scheme to deal with fragmentation ...  */


    if (recycled_nodes_link_list) /* if we have recycled nodes available, use them. */
    {
        tree = recycled_nodes_link_list;
        recycled_nodes_link_list = RIGHT_NODE(recycled_nodes_link_list); /* remove this node from recycled list, ie go to the right */
    }
    else    /* if no recycled nodes, use allocated nodes. */
        tree = &allocated_nodes_block[--number_of_allocated_nodes];

    memset(tree, 0, sizeof(*tree));      /* set all fields to 0, no need to worry about setting each fields, memset is quite fast. */
    return tree;
}

/* Delete allocated blocks of nodes ... */
void free_blocks()
{
    recycled_nodes_link_list = allocated_nodes_block; /* save current block. */
    while (recycled_nodes_link_list)    /* while there are blocks to be freed. */
    {   /* retrieve previous block. */
        recycled_nodes_link_list = *(ordered_set_tree_node_type **)&allocated_nodes_block[NODE_BLOCK_SIZE];
        free(allocated_nodes_block); /* free current block*/
        allocated_nodes_block = recycled_nodes_link_list;  /* set previous block for deletion. */
    }
}

/*
    As predefined by the assignment:
        creates an empty linear ordered set

    Because we need to keep track of 'two' trees, and we really shouldn't introduce
    anymore structures, we will simply represent this by a 'main or root' node
    where its left child points to the tree containing the orders and
    the right child points to the tree containing the keys
    where the leaves of each tree point to each other, so they can update each other.
*/
/* we'll use macro functions to keep track of which node is which tree. */
#define ORDER_TREE LEFT_NODE
#define KEY_TREE RIGHT_NODE
ordered_set_tree_node_type * create_order();
ordered_set_tree_node_type * create_order()
{
    ordered_set_tree_node_type *tree = allocate_node();      /* root node  */
    ORDER_TREE(tree) = allocate_node();                      /* order tree */
    KEY_TREE(tree) = allocate_node();                        /* key tree   */

    return tree;
}

/* return the nearest leaf of a giving key, leave->key may or may not equal to key */
ordered_set_tree_node_type *find_node(ordered_set_tree_node_type *key_order, key_type key)
{
    while (IS_TREE(key_order)) /* while we are not in a leaf. */
        if (key < KEY(key_order))
            key_order = LEFT_NODE(key_order);
        else
            key_order = RIGHT_NODE(key_order);
    
    return key_order;
}

/* print error message and exit */
void error(char *message)
{
    printf("Error: %s\n", message);
    exit(-1);
}

void check_ordered_set_tree(ordered_set_tree_node_type *tree)
{
    if (!tree || !LEFT_NODE(tree) || !RIGHT_NODE(tree))
        error("An improper 'ordered_set_tree' was giving!");
}

/*
    A Left Rotation on node c is done by manipulating its child pointers,
    fundamentally node c isn't really moved at all, the relationship between its children are changed.

    we move the right-right node up one level and the left node down one level,
    and insert the previous right child in the left, now we just need to update the pointers
    also note that the previous right-left child switch places.

    @note: unlike a regular rotation we have to update the parent node when a node changes parent
    this occurs in 2 places, when we move one node a level up and another a level down.

    We also need to update the keys.
 */
void left_rotation(ordered_set_tree_node_type *);
void left_rotation(ordered_set_tree_node_type *tree)
{
    ordered_set_tree_node_type *left_node = LEFT_NODE(tree); /* back-up original left node */
    key_type tree_key = KEY(tree); /* back up key of root to swap with pivoting node */

    /* update keys. */
    KEY(tree) = KEY(RIGHT_NODE(tree));      /* move key of right node up */
    KEY(RIGHT_NODE(tree)) = tree_key;       /* move key of root node down to the left. */

    LEFT_NODE(tree) = RIGHT_NODE(tree);     /* move right node to the left, middle insertion step. */

    RIGHT_NODE(tree) = RIGHT_NODE(RIGHT_NODE(tree));    /* move right-right node up ... */
    PARENT_NODE(RIGHT_NODE(tree)) = tree;               /* update its parent node*/

    RIGHT_NODE(LEFT_NODE(tree)) = LEFT_NODE(LEFT_NODE(tree));   /* move original right->left node to new left->right  */

    LEFT_NODE(LEFT_NODE(tree)) = left_node;             /* move original left down another level to the left  */
    PARENT_NODE(left_node) = LEFT_NODE(tree);           /* Update its parent */
}

/*
    Very similar to a Left rotation just that we invert the direction.

    We move the left-left node up 1 level, the right node down 1 level and
    insert the previous left node in the right. again the previous left-right
    node switches places.
 */
void right_rotation(ordered_set_tree_node_type *);
void right_rotation(ordered_set_tree_node_type *tree)
{
    ordered_set_tree_node_type *right_node = RIGHT_NODE(tree); /* back-up original right node. */
    key_type tree_key = KEY(tree); /* back up key of root to swap with pivoting node */

    RIGHT_NODE(tree)      = LEFT_NODE(tree);        /* move left node to the right, middle insertion step. */
    KEY(tree)             = KEY(RIGHT_NODE(tree));  /* move left key up. */
    KEY(RIGHT_NODE(tree)) = tree_key;               /* move root key down.  */

    LEFT_NODE(tree) = LEFT_NODE(LEFT_NODE(tree));   /* move the left-left node up one level. */
    PARENT_NODE(LEFT_NODE(tree)) = tree;            /* Update its parent. */

    LEFT_NODE(RIGHT_NODE(tree)) = RIGHT_NODE(RIGHT_NODE(tree)); /* flip original left->right to right side. */
    RIGHT_NODE(RIGHT_NODE(tree)) = right_node;      /* move original right node down one level. */
    PARENT_NODE(right_node) = RIGHT_NODE(tree);     /* update its parent. */
}
/*
    Balance a tree either key or order by height using the parent field
    to go up to the root, whose parent is NULL.

    we have to make sure that the height of a node's children don't differ by more than 1.
    if the height differs by 2, we need apply rotations to regain our height property.

    4 possibilities:
        left tree is longer
            left-left tree is longer
            left-right tree is longer
        right tree is longer
            right-right tree is longer
            right-left tree is longer
 */
void balance_tree(ordered_set_tree_node_type *);
void balance_tree(ordered_set_tree_node_type *tree)
{
    int height, old_height;
    while (tree) /* while we are not at the root. */
    {
        height = HEIGHT(LEFT_NODE(tree)) - HEIGHT(RIGHT_NODE(tree));
        old_height = HEIGHT(tree);
        if (height == 2) /* left side is heavier */
        {
            if ((HEIGHT(LEFT_NODE(LEFT_NODE(tree))) - HEIGHT(RIGHT_NODE(tree))) == 1)  /* left-left heavy tree */
            {
                right_rotation(tree); /* single right rotation to correct, we need to update 2 heights, tree & tree->left */
                HEIGHT(RIGHT_NODE(tree)) = HEIGHT(LEFT_NODE(RIGHT_NODE(tree))) + 1;
                /* since we did a right rotation which changed the left child the new height is the height of this new child + 1, the right child should be smaller */
                HEIGHT(tree) = HEIGHT(RIGHT_NODE(tree)) + 1; /* the new height is that of the new right child plus 1 */
            }
            else /* left-right heavy tree, 2 rotations required. */
            {
                left_rotation(LEFT_NODE(tree)); /* transform into left-left heavy tree */
                right_rotation(tree);           /* balance */
                height = HEIGHT(LEFT_NODE(LEFT_NODE(tree))) + 1;
                HEIGHT(LEFT_NODE(tree))     = height;
                HEIGHT(RIGHT_NODE(tree))    = height;
                HEIGHT(tree)                = height + 1;
            }
        }
        else if (height == -2) /* right side is heavier. */
        {
            if (HEIGHT(RIGHT_NODE(RIGHT_NODE(tree))) - HEIGHT(LEFT_NODE(tree)) == 1) /* right-right heavy tree */
            {
                left_rotation(tree);
                HEIGHT(LEFT_NODE(tree)) = HEIGHT(RIGHT_NODE(LEFT_NODE(tree))) + 1;
                HEIGHT(tree) = HEIGHT(LEFT_NODE(tree)) + 1;
            }
            else /* right-left heavy tree */
            {
                right_rotation(RIGHT_NODE(tree)); /* transform to right-right heavy tree */
                left_rotation(tree);
                height = HEIGHT(RIGHT_NODE(RIGHT_NODE(tree))) + 1;
                HEIGHT(LEFT_NODE(tree)) = height;
                HEIGHT(RIGHT_NODE(tree)) = height;
                HEIGHT(tree) = height + 1;
            }
        }
        else  /* heights didn't differ by 2, update anyway.  */
        {
            if (HEIGHT(LEFT_NODE(tree)) > HEIGHT(RIGHT_NODE(tree)))
                HEIGHT(tree) = HEIGHT(LEFT_NODE(tree)) + 1;
            else
                HEIGHT(tree) = HEIGHT(RIGHT_NODE(tree)) + 1;
        }

        if (HEIGHT(tree) == old_height) /* if the height didn't changed we no longer need to continue.  */
            return ;

        tree = PARENT_NODE(tree); /* go up to parent. */
    }
}


/*
    The insert node mechanism is 'almost' identical for both trees,
    except when we insert the an ordered node we don't yet have a key node.
 */
ordered_set_tree_node_type*
        _insert_node(ordered_set_tree_node_type *tree, /* a leaf in either tree .. */
                     ordered_set_tree_node_type *leaf, /* a pointer to the other leaf, or NULL when working with ordered leafs. */
                     key_type key, /* the key for this new node, 0 when working with ordered leaves. */
                     int before    /* the order for this new node. */)
{
    ordered_set_tree_node_type          /* create new set of leaves. */
            *old_leaf = allocate_node(),
            *new_leaf = allocate_node();

    HEIGHT(tree)          = 1;
    PARENT_NODE(old_leaf) = tree;
    PARENT_NODE(new_leaf) = tree;

    KEY(new_leaf)       = key;      /* set keys. */
    KEY(old_leaf)       = KEY(tree);

    VALUE(old_leaf) = VALUE(tree); /* copy address of other node. */
    VALUE(VALUE(old_leaf)) = old_leaf; /* goto to other node and update address.  */

    if (leaf) /* check that we are inserting into a key tree! */
    {
        VALUE(new_leaf) = leaf; /* link new_leaf to order leaf */
        VALUE(leaf) = new_leaf; /* link leaf into key leaf */
    }

    if (before)
    {
        LEFT_NODE(tree) = new_leaf;
        RIGHT_NODE(tree) = old_leaf;
    }
    else
    {
        KEY(tree) = key; /* update current key, since previous key may be smaller. */
        LEFT_NODE(tree) = old_leaf;
        RIGHT_NODE(tree) = new_leaf;
    }

    balance_tree(PARENT_NODE(tree));

    return new_leaf;
}

void _insert_key(ordered_set_tree_node_type *tree, key_type key_a, key_type key_b, int before)
{
    #ifdef SAFE_MODE
        check_ordered_set_tree(tree);
    #endif

    ordered_set_tree_node_type *temp = find_node(KEY_TREE(tree), key_b); /* locate key b */

    if (KEY(temp) != key_b)                  /* if key b couldn't be found emit error and exit. */
        error("Key could not be located!");
    if (KEY(temp) == key_a)
        error("Trying to insert duplicate keys!");

    tree = find_node(KEY_TREE(tree), key_a);  /* locate best node to insert key a. */
    /* insert key_a with new node from the ordered tree. */
    _insert_node(
            tree,
            _insert_node(
                    VALUE(temp), /* move to order tree. */
                    NULL,
                    0,
                    before),
            key_a,
            (key_a < KEY(tree)));
}

#define BEFORE 1
#define AFTER 0
/*
    As predefined by the assignment:
        inserts the key a immediately before key b in the ordered set.
 */
void insert_before(ordered_set_tree_node_type *tree, key_type key_a, key_type key_b)
{   _insert_key(tree, key_a, key_b, BEFORE); }

/*
    As predefined by the assignment:
        inserts the key a immediately after key b in the ordered set.
 */
void insert_after(ordered_set_tree_node_type *tree, key_type key_a, key_type key_b)
{   _insert_key(tree, key_a, key_b, AFTER); }


/*
    Insert a new node in the ordered tree either on the top, largest order if before is 0
    or at the bottom least ordered if before is non-zero.
 */
void _insert_ordered_value(ordered_set_tree_node_type *tree, key_type key, int before)
{
    #ifdef SAFE_MODE
        check_ordered_set_tree(tree);
    #endif
    
    if (IS_EMPTY_TREE(KEY_TREE(tree))) /* if trees are empty then just have them point to each other ... */
    {
        VALUE(KEY_TREE(tree)) = ORDER_TREE(tree);
        VALUE(ORDER_TREE(tree)) = KEY_TREE(tree);
        KEY(KEY_TREE(tree)) = key;
        
        return ;
    }
    
    ordered_set_tree_node_type *ordered_tree = ORDER_TREE(tree);

    if (before)
        while (IS_TREE(ordered_tree)) /* while we are a tree ie not a leaf, go down to the left, smallest value. */
            ordered_tree = LEFT_NODE(ordered_tree);
    else
        while (IS_TREE(ordered_tree)) /* go down the right ie largest value. */
            ordered_tree = RIGHT_NODE(ordered_tree);

    tree = find_node(KEY_TREE(tree), key);

    if (KEY(tree) == key)
        error("Trying to insert duplicate key!");

    _insert_node(
            tree,
            _insert_node(
                ordered_tree,
                NULL,
                0,
                before),
            key,
            (key < KEY(tree))
    );
}
/*
    As predefined by the assignment:
        inserts the key a as largest element in the ordered set
 */
void insert_top(ordered_set_tree_node_type *tree, key_type key)
{   _insert_ordered_value(tree, key, AFTER);    }

/*
    As predefined by the assignment:
        inserts the key a as smallest element in the ordered set
 */
void insert_bottom(ordered_set_tree_node_type *tree, key_type key)
{
    _insert_ordered_value(tree, key, BEFORE);
}



/*
    The delete mechanism is identical in both trees ...
 */
void _delete_node(ordered_set_tree_node_type *tree)
{
    ordered_set_tree_node_type *parent = PARENT_NODE(tree); /* go up to parent */

    if (LEFT_NODE(parent) == tree) /* we are deleting the left child, so we need to move the right child nodes up. */
    {
        KEY(parent) = KEY(RIGHT_NODE(parent));

        LEFT_NODE(parent) = LEFT_NODE(RIGHT_NODE(parent)); /* move right-left node up */
        recycle_node(tree);         /* recycle left node */

        tree = RIGHT_NODE(parent);  /* save for recycling. */
        RIGHT_NODE(parent) = RIGHT_NODE(RIGHT_NODE(parent)); /* move right-right node up */

        recycle_node(tree);         /* recycle right node */
    }
    else /* we are deleting the right child so we need to move the left child up. */
    {
        KEY(parent) = KEY(LEFT_NODE(parent));

        RIGHT_NODE(parent) = RIGHT_NODE(LEFT_NODE(parent)); /* move the left-right node up  */
        recycle_node(tree); /* recycle right node */

        tree = LEFT_NODE(parent); /* save left node for recycling. */
        LEFT_NODE(parent) = LEFT_NODE(LEFT_NODE(parent)); /* move left-left node up */

        recycle_node(tree); /* recycle left child */
    }

    if (IS_TREE(parent)) /* check if new node is a tree */
    {
        PARENT_NODE(LEFT_NODE(parent)) = parent; /* update parent of each child. */
        PARENT_NODE(RIGHT_NODE(parent)) = parent;
    }
    else /* if its leaf we have to update the pointer in the order for leaves to point to each other. */
    {
        VALUE(VALUE(parent)) = parent;
        HEIGHT(parent) = 0;
        parent = PARENT_NODE(parent); /* move one node up to start balancing. */
    }

    balance_tree(parent);
}

/*
    As predefined by the assignment:
         deletes the key a from the ordered set
 */
void delete_o(ordered_set_tree_node_type *tree, key_type key)
{
    #ifdef SAFE_MODE
        check_ordered_set_tree(tree);
    #endif

    tree = find_node(KEY_TREE(tree), key);
    if (KEY(tree) != key)
        error("Key could not be found for deletetion!");

    _delete_node(VALUE(tree));
    _delete_node(tree);
}

static ordered_set_tree_node_type   /*  list of node pointers used to track path form leave to root, 100 should suffice. */
        *path_a[100] = {NULL},
        *path_b[100] = {NULL};
/*
    Giving the depth of two nodes whose path to the root are encoded in path_a and path_b respectively,
     apply a binary search to find the first common node.
     note that the paths include the leaves.

     return the index of which both nodes are common from the top of the array, since the two arrays
     may be of varying length, note 0 is return whether or not a match was found, but considering
     we are working with a binary tree we should always get a match and 0 just means both
     nodes are one in the same.
 */
unsigned int find_first_common_node(unsigned int node_a_depth, unsigned int node_b_depth)
{
    unsigned int
            middle_index,
            minimum_index = 0,
            maximum_index; /* the maximum index depends on the shortest path. */

    /*  before we can begin our search we must first start at the same depth. */
    ordered_set_tree_node_type /* the two paths leveled so they start at the same depth. */
            **leveled_path_a,
            **leveled_path_b;

    if (node_a_depth < node_b_depth) /* node a has a shorter path so we have to move node b up to nodes a level. */
    {
        maximum_index = node_a_depth;
        leveled_path_a = path_a;
        leveled_path_b = path_b + (node_b_depth - node_a_depth);
    }
    else
    {
        maximum_index = node_b_depth;
        leveled_path_a = path_a + (node_a_depth - node_b_depth);
        leveled_path_b = path_b;
    }

    node_a_depth = maximum_index; /* save maximum depth so we can return index from the top of each array ... */
    while (minimum_index < maximum_index)
    {
        middle_index = minimum_index + ((maximum_index - minimum_index) / 2);
        if (leveled_path_a[middle_index] == leveled_path_b[middle_index]) /* if they equal go down. */
            maximum_index = middle_index;
        else /* if they don't equal go up. */
            minimum_index = middle_index + 1;
    }

    return (node_a_depth - maximum_index);   /* return index with respects to the 'root' or top node. */
}
/*
    As predefined by the assignment:
        returns 1 if key a occurs before key b in the ordered set, 0 else.

    Unfortunately because of the rotations we are unable to keep track of the each nodes depth.
    So we have to locate both keys, jump to the order tree and record the entire path up to the root
    on an array, afterward we simply search for the point at which both paths intercept, their order
    determines which is greater, note that we can apply binary search.
 */
int is_before(ordered_set_tree_node_type *tree, key_type key_a, key_type key_b)
{
    #ifdef SAFE_MODE
        check_ordered_set_tree(tree);
    #endif
    if (key_a == key_b) /* if trying to query identical just return 0, regardless of whether or not they exist */
        return 0;

    ordered_set_tree_node_type
            *temp = find_node(KEY_TREE(tree), key_a);

    if (KEY(temp) != key_a)
        error("Could not locate key!");

    unsigned int
            distance_from_root = 0,
            node_a_depth       = 0,
            node_b_depth       = 0;

    temp = VALUE(temp); /* JUMP to order tree. */
    path_a[node_a_depth++] = temp; /* record path up to root for key a. */
    while ((temp = PARENT_NODE(temp)))
        path_a[node_a_depth++] = temp;

    temp = find_node(KEY_TREE(tree), key_b);
    if (KEY(temp) != key_b)
        error("Could not locate key!");

    temp = VALUE(temp); /* JUMP to order tree. */
    path_b[node_b_depth++] = temp;
    while ((temp = PARENT_NODE(temp)))  /* record path up to root for key b. */
        path_b[node_b_depth++] = temp;

    distance_from_root = find_first_common_node(node_a_depth, node_b_depth);
    #ifdef SAFE_MODE
        if (path_a[(node_a_depth - distance_from_root)] != path_b[(node_b_depth - distance_from_root)])
            error("Did not properly locate common node!");
    #endif

    node_a_depth = node_a_depth - distance_from_root;       /* locate index of common node */
    tree = path_a[node_a_depth];                            /* save common node so we can check its children */
    node_a_depth -= 1;                                      /* get the previous node's index for path a, to see if its the left child*/
    node_b_depth = node_b_depth - distance_from_root - 1;   /* get the previous node's index for path b, to see if its the right child */

    return ((LEFT_NODE(tree)  == path_a[node_a_depth]) &&
            (RIGHT_NODE(tree) == path_b[node_b_depth]));
}

typedef ordered_set_tree_node_type o_t;
#define key_t key_type;


long int p(long int q)
{ return( (1247 * q + 104729) % 300007 );
}

int main()
{  long i; o_t *o;
    printf("starting \n");
    o = create_order();
    printf("done creating order \n");
    for(i=100000; i>=0; i--)
        insert_bottom( o, p(i) );    
    printf("done inserting ... \n");
    for(i=100001; i< 300007; i+=2 )
    {  insert_after(o, p(i+1), p(i-1) );
        insert_before( o, p(i), p(i+1) );
    }
    printf("inserted 300000 elements.\n");
    for(i = 250000; i < 300007; i++ )
        delete_o( o, p(i) );
    printf("deleted 50000 elements.\n");
    insert_top( o, p(300006) );
    for(i = 250000; i < 300006; i++ )
        insert_before( o, p(i) , p(300006) );
    printf("reinserted. now testing order\n");
    for( i=0; i < 299000; i +=42 )
    {  if( is_before( o, p(i), p(i+23) ) != 1 )
    {  printf(" found error (1) \n"); exit(0);
    }
    }
    for( i=300006; i >57; i -=119 )
    {  if( is_before( o, p(i), p(i-57) ) != 0 )
    {  printf(" found error (0) \n"); exit(0);
    }
    }
    printf("finished. no problem found.\n");
}


//int main (int argc, const char * argv[])
//{
//    o_t *ordered_set = create_order();
//
//    unsigned int index = 0;
//    for (index = 200; index; index--)
//        insert_bottom(ordered_set, index);
//    insert_bottom(ordered_set, index);
//
//    for (index = 1000; index < 1400; index++)
//        insert_top(ordered_set, index);
//
//    for (index = 201; index < 400; index++)
//        insert_after(ordered_set, index, (index - 1));
//
//    for (index = 999; index >= 400; index--)
//        insert_before(ordered_set, index, (index + 1));
//
//    for (index = 10; index < 1000; index += 2)
//        delete_o(ordered_set, index);
//    for (index = 10; index < 1000; index += 2)
//        insert_before(ordered_set, index, index + 1);
//
//
//    for (index = 1; index < 1399; index++)
//        if (
//             (!is_before(ordered_set, index, index + 1)) ||
//             (is_before(ordered_set, index,  index - 1)) ||
//             (is_before(ordered_set, index,  0))         ||
//             (!is_before(ordered_set, index, 1399))
//           )
//        {
//            printf("Failed to properly insert %u", index);
//            exit(-1);
//        }
//
//    for (index = 1000; index < 1400; index++)
//        delete_o(ordered_set, index);
//
//    for (index = 1000; index < 1400; index++)
//        if (KEY(find_node(ordered_set, index)) == index)
//        {
//            printf("Failed to delete %u", index);
//            exit(-1);
//        }
//
//    printf("ok.\n");
//    // free_blocks();
//    return 0;
//}
