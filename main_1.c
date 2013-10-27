//
//  main.c
//  adv_data_structures_hw_2
//
//  Created by Samy Vilar
//

#include <stdio.h>
#include <stdlib.h>
#include <string.h>


//#define ENABLE_FRACTIONAL_CASCADING

#define WORD int
typedef WORD signed_word;
typedef unsigned WORD unsigned_word;
typedef signed_word key_type;
#undef WORD


/*  AS PRE-DEFINE BY THE ASSIGNMENT:
        Represents a half open rectangle
        where we have a (lower left) corner
        and (upper, right) corner
*/
typedef struct rectlist
{
    struct rectlist
            *next; /* pointer to the next rectangle, make it first so we don't have to dereference it. */

    signed_word
       left,
       lower,  /* left lower corner of the rectangle (x, y)  */
       right,
       upper; /* right upper corner of the rectangle (x, y) */

} rectlist;
#define next_rectangle(rec_list) (*(rectlist **)rec_list)
#define set_next_rectangle(rec_list, value) (next_rectangle(rec_list) = value)
#define left(rec_list)  (rec_list->left)
#define lower(rec_list) (rec_list->lower)
#define right(rec_list) (rec_list->right)
#define upper(rec_list) (rec_list->upper)

/*
    Link List of interval types used to store intervals at each appropriate node.
 */
typedef struct interval_link_list_type
{
    struct interval_link_list_type
            *prev; /* pointer to previous values or NULL, make it first so we don't have to dereference it. */

    key_type
            endpoint_a,
            endpoint_b;      /* endpoints of our interval a <= b */

    rectlist *rectangle;
} interval_link_list_type;
#define prev_interval(intervals) (*(interval_link_list_type **)intervals)
#define set_prev_interval(interval, value) (prev_interval(interval) = value)
#define end_point_a(interval) (interval->endpoint_a)
#define set_end_point_a(interval, point_a) (end_point_a(interval) = point_a)
#define end_point_b(interval) (interval->endpoint_b)
#define set_end_point_b(interval, point_b) (end_point_b(interval) = point_b)
#define rectangle(interval) (interval->rectangle)
#define set_rectangle(interval, value) (rectangle(interval) = value)


/* Manage intervals ...  */
#define INTERVAL_LIST_BLOCK_SIZE 512
static interval_link_list_type
        *interval_list_block     = NULL,
        *interval_list_recycled  = NULL;

static unsigned_word
        number_of_interval_lists_allocated  = 0;

void recycle_interval_link_list(interval_link_list_type *interval)
{
    set_prev_interval(interval, interval_list_recycled);
    interval_list_recycled = interval;
}

interval_link_list_type *get_new_interval_link_list()
{
    interval_link_list_type *temp;

    if (!number_of_interval_lists_allocated)
    {
        temp = interval_list_block;
        interval_list_block = malloc((sizeof(interval_link_list_type) * INTERVAL_LIST_BLOCK_SIZE) + sizeof(void *));
        number_of_interval_lists_allocated = INTERVAL_LIST_BLOCK_SIZE;
        *(interval_link_list_type **)(&interval_list_block[INTERVAL_LIST_BLOCK_SIZE]) = temp;
    }

    if (interval_list_recycled)
    {
        temp = interval_list_recycled;
        interval_list_recycled = prev_interval(interval_list_recycled);
    }
    else
        temp = &interval_list_block[--number_of_interval_lists_allocated];

    return temp;
}


void free_interval_blocks()
{
    interval_link_list_type *blocks = interval_list_block;
    while (blocks)
    {
        interval_list_block = *(interval_link_list_type **)(&blocks[INTERVAL_LIST_BLOCK_SIZE]);
        free(blocks);
        blocks = interval_list_block;
    }
}
/***********************************************************************************************************/


/*
    represents a 2 dimensional segment tree, where the first dimension is the
    x axis and the second is the y-axis.

    Convention:
        key < tree->left->key or key >= tree->right->key
        tree->left == NULL is an empty tree
        (tree->right == NULL and tree->left != NULL) is a leaf and the left node contains a pointer to the object
        (tree->right != NULL and tree->left != NULL) is a complete tree
        tree->upper == NULL has no parent node that contains intervals.
        tree->upper != NULL

    each node contains another segment_tree for the second dimension (y).
 */
typedef struct two_d_segment_tree_node_type
{
    struct two_d_segment_tree_node_type
            *right,  /* right sub-tree */
            *left,   /* left sub-tree  */
            *upper;  /* upper node that contains intervals otherwise NULL */

    key_type
            key; /* this nodes key. */

    struct two_d_segment_tree_node_type
            *y_axis;        /* second segment tree for the y-axis. */

    interval_link_list_type
            *interval_list; /* link list of all intervals that fall through this node.  */

} two_d_segment_tree_node_type;
#define right_node(tree) (*(two_d_segment_tree_node_type **)tree)
#define set_right_node(tree, value) (right_node(tree) = value)
#define left_node(tree) (tree->left)
#define set_left_node(tree, value) (left_node(tree) = value)
#define upper_node(tree) (tree->upper)
#define set_upper_node(tree, value) (upper_node(tree) = value)
#define key(tree) (tree->key)
#define set_key(tree, value) (key(tree) = value)
#define y_axis(tree) (tree->y_axis)
#define set_y_axis(tree, value) (y_axis(tree) = value)
#define interval_list(tree) (tree->interval_list)
#define set_interval_list(tree, value) (interval_list(tree) = value)
#define is_tree right_node
#define object left_node
#define set_object set_left_node




/********************* Node Management. **********************************************/
#define NODE_BLOCK_SIZE 256

static two_d_segment_tree_node_type
        *block_allocated_nodes = NULL, /* allocated blocks of nodes */
        *recycled_nodes        = NULL; /* link list of recycled nodes to be re used. */

static unsigned int number_of_allocated_nodes = 0; /* number nodes available on the current block. */

/* recycle nodes, though we don't need it here. */
void recycle_node(two_d_segment_tree_node_type *tree)
{
    set_right_node(tree, recycled_nodes); // save previously recycled nodes
    recycled_nodes = tree;        // recycle this node.

    /* recycle the intervals */
    interval_link_list_type *interval = interval_list(tree);
    while (interval)
    {
        interval = prev_interval(interval); // save previous intervals
        recycle_interval_link_list(interval_list(tree)); // delete this interval
        set_interval_list(tree, interval); // restore previous intervals for recycling.
    }
}

/* we only need two stacks. */
static two_d_segment_tree_node_type
        *stacks[2][100]              = {{NULL}}; /* common stack used among all the sub routines. */

static unsigned_word
        stack_indices[2] = {0};

#define reset_stack(index) (stack_indices[index] = 0)
#define push(st_index, value) (stacks[st_index][(stack_indices[st_index])++] = value)
#define pop(st_index) (stacks[st_index][--(stack_indices[st_index])])
#define stack_has_element(st_index) (stack_indices[st_index])

typedef unsigned_word stack_type;
/*
    Recycle an entire tree, it does not deallocate any of the blocks!
 */
void recycle_tree(two_d_segment_tree_node_type *tree)
{
    reset_stack(0);
    push(0, tree);
    while (stack_has_element(0))
    {
        tree = pop(0);
        if (is_tree(tree)) /* check that its not a leaf */
        {
            push(0, right_node(tree));
            push(0, left_node(tree));
        }

        if  (y_axis(tree))
            push(0, y_axis(tree));

        recycle_node(tree);
    }
}

void free_node_blocks()
{
    two_d_segment_tree_node_type *blocks = block_allocated_nodes;
    while (blocks)
    {
        block_allocated_nodes = *(two_d_segment_tree_node_type **)(&blocks[NODE_BLOCK_SIZE]);
        free(blocks);
        blocks = block_allocated_nodes;
    }
}


two_d_segment_tree_node_type *get_new_empty_tree()
{
    two_d_segment_tree_node_type *tree;

    if (!number_of_allocated_nodes)
    {   /* allocate block of nodes. */
        /* at the end of the block we will add the memory address of the previous block so we can free it later on ... */
        tree = block_allocated_nodes;
        block_allocated_nodes = malloc((sizeof(two_d_segment_tree_node_type) * NODE_BLOCK_SIZE) + sizeof(void *));
        *((two_d_segment_tree_node_type **)(&block_allocated_nodes[NODE_BLOCK_SIZE])) = tree;

        number_of_allocated_nodes = NODE_BLOCK_SIZE;
    }

    if (recycled_nodes) /* use previously recycled nodes. */
    {
        tree = recycled_nodes; // get a recycled node
        recycled_nodes = right_node(recycled_nodes);  // remove the element from the recycled nodes list.
    }
    else
        tree = &block_allocated_nodes[--number_of_allocated_nodes];


    set_left_node(tree, NULL);
    set_right_node(tree, NULL);
    set_interval_list(tree, NULL);
    set_y_axis(tree, NULL);
    set_upper_node(tree, NULL);

    return tree;
}
/**********************************************************************************************************/

/*****************************************************************************************
*    Sort all the elements using merge sort bottom up ...                               *
*    Basically initially treat list of sub-lists of length 1 and merge ...              *
*    then increment to lists of length 2 and merge                                      *
*    keep track of the number merges if only merged once then we are done.              *
*****************************************************************************************/
#define next right_node
#define set_next set_right_node
#define value key
#define set_value set_key
two_d_segment_tree_node_type *sort(two_d_segment_tree_node_type *values)
{
    two_d_segment_tree_node_type
            *list_1        = NULL, /* used to store list 1 for merging */
            *list_2        = NULL, /* used to store list 2 for merging */
            *current_node  = NULL, /* used to store the current sorted node to be appending*/
            *sorted_list   = NULL; /* used to store the sorted nodes */

    unsigned_word
            list_1_length      = 0,
            list_2_length      = 0,
            number_of_merges   = 0,
            index              = 0,
            step_size          = 1;

    while (1)
    {
        list_1 = values;
        number_of_merges = 0;
        values = NULL;
        sorted_list = NULL;

        /* Merge a set of lists each made of step-size length ... */
        while (list_1)
        {
            number_of_merges++;
            list_2 = list_1;
            for (index = 0; (list_2 && (index < step_size)); index++)       /* generate two list each of step-size length. */
                list_2 = next(list_2);

            list_1_length = index;
            list_2_length = step_size;

            /* Merge 2 lists of length step size. (list_1 and list_2) */
            while (list_1_length || (list_2_length && list_2))
            {   /* First look for a current node depending on the state of the two lists to merge */
                if (!list_1_length)                      /* list_1 is empty so the current node must come from list_2 */
                {
                    current_node = list_2;
                    list_2 = next(list_2);
                    list_2_length--;
                }
                else if (!list_2_length || !list_2)      /* list_2 is empty so the current node must come from list_1 */
                {
                    current_node = list_1;
                    list_1 = next(list_1);
                    list_1_length--;
                }
                else if (value(list_1) < value(list_2))     /* neither is NULL so compared keys ... */
                {
                    current_node = list_1;
                    list_1 = next(list_1);
                    list_1_length--;
                }
                else
                {
                    current_node = list_2;
                    list_2 = next(list_2);
                    list_2_length--;
                }


                if (sorted_list) /* if we already have merged previous lists. */
                        set_next(sorted_list, current_node); /* append new value to sorted list */
                else
                    values = current_node; /* save initial point to list of lists ... */

                sorted_list = current_node; /* move the list forward */
            }

            list_1 = list_2; /* continue to merge other lists ... */
        }

        set_next(sorted_list, NULL);  /* terminate list of sorted lists */

        if (number_of_merges <= 1) /* if we only merged once we are done ... */
            break ;

        step_size *= 2;
    }

    return values;
}
/*
    creates a balanced tree from a list of
    rectangles ...
 */
#define INTERVAL_LIST 1
#define RECTANGLE_LIST 0
two_d_segment_tree_node_type *create_balanced_tree(rectlist *data, int dimension)
{
    if (!data) /* No data so just create an empty tree. */
        return get_new_empty_tree();

    two_d_segment_tree_node_type
            *end_points = NULL,
            *temp       = NULL; /* Store all the end points in a list of tree nodes ... */

    interval_link_list_type *interval_lists =
            dimension ? (interval_link_list_type *)data
                      : NULL;

    if (interval_lists) /* if dimension is 1 its the y axis, use endpoints. */
        while (interval_lists)
        {
            temp = get_new_empty_tree();
            set_next(temp, end_points);
            set_value(temp, end_point_a(interval_lists));
            end_points = temp;

            temp = get_new_empty_tree();
            set_next(temp, end_points);
            set_value(temp, end_point_b(interval_lists));
            end_points = temp;

            interval_lists = prev_interval(interval_lists);
        }
    else /* dimension must be 0 the x-axis use rectangle left and right ... */
        while (data)
        {
            temp = get_new_empty_tree();  /* get new node */
            set_next(temp, end_points);   /* link new node to previous set of nodes. */
            set_value(temp, left(data));    /* add left end point as key to the node */
            end_points = temp;            /* make the new node the head of the list. */

            temp = get_new_empty_tree();  /* repeat as above for the other end point */
            set_next(temp, end_points);
            set_value(temp, right(data));
            end_points = temp;

            data = next_rectangle(data);
        }

    end_points = sort(end_points);
    /* Build a balanced binary tree using a sorted sequence values. */
    typedef struct stack_item
    {
        two_d_segment_tree_node_type
                *tree_node,             /* The actual node used within the tree */
                *smallest_parent_node;  /* This stores the smallest parent node
                                         * which will be set as a comparison key from a
                                         * found leave                        */
        unsigned int number;    /* The number of leaves the node will contain */

    } stack_item;

    stack_item
            current,
            left,
            right;

    two_d_segment_tree_node_type
            *root;

    unsigned_word number_of_items = 0; /* calculate the total number items and remove any duplicates. */
    temp = end_points;
    while (temp)
    {
        root = temp;
        while ((temp = next(temp)) && (value(root) == value(temp)));
        set_next(root, temp);

        number_of_items++;
    }

    static stack_item stack[100]; /* our stack of items */
    unsigned_word stack_index = 0;

    root                         = get_new_empty_tree(); /* the root of our tree */
    current.tree_node            = root;                 /* set tree node */
    current.smallest_parent_node = NULL;                 /* it has no parent */
    current.number               = number_of_items;      /* it will hold all our leaves. */

    stack[stack_index++] = current; /* push the root unto the stack */
    while (stack_index)             /* while the stack is not empty */
    {
        current = stack[--stack_index]; /* pop an item */
        if (current.number > 1)
        {
            left.tree_node = get_new_empty_tree(); /* create new tree node for left sub-tree */
            left.smallest_parent_node = current.smallest_parent_node; /* keep track of the smallest parent node */
            left.number = current.number / 2;

            right.tree_node = get_new_empty_tree();
            right.smallest_parent_node = current.tree_node; /* the smallest node from the right sub tree
                                                                will always be the parent node */
            right.number = current.number - left.number;

            set_left_node((current.tree_node), (left.tree_node));
            set_right_node((current.tree_node), (right.tree_node));

            /* Fraction Cascading requires that we set up back pointers to upper node,
                        since we will be traversing upwards from leaves.*/
            #ifdef ENABLE_FRACTIONAL_CASCADING
                set_upper_node((left.tree_node), (current.tree_node));
                set_upper_node((right.tree_node), (current.tree_node));
            #endif

            stack[stack_index++] = right;
            stack[stack_index++] = left;
        }
        else /* reached a leave. */
        {
            set_left_node((current.tree_node), NULL);
            set_right_node((current.tree_node), NULL);
            set_key((current.tree_node), key(end_points));

            if (current.smallest_parent_node) /* There is an interior node to be set. */
                set_key((current.smallest_parent_node), key(end_points));

            temp = end_points;
            end_points = right_node(end_points);
            recycle_node(temp);
        }
    }

    return root;
}
#undef next
#undef set_next
#undef value


/*  Attach a segment to a link list of intervals. */
void attach_segment(
        two_d_segment_tree_node_type *tree,
        key_type endpoint_a,
        key_type endpoint_b,
        rectlist *rectangle)
{
    interval_link_list_type *temp = get_new_interval_link_list();
    set_prev_interval(temp, interval_list(tree)); // save previous intervals

    set_end_point_a(temp, endpoint_a);
    set_end_point_b(temp, endpoint_b);
    set_rectangle(temp, rectangle);

    set_interval_list(tree, temp); // add new interval
}

/*
    Locate node and insert segment.
 */
#define INSERT_INTO_PARENTS 1
#define DO_NOT_INSERT_INTO_PARENTS 0
void insert_segment(
        two_d_segment_tree_node_type *tree,
        key_type key_a,
        key_type key_b,
        rectlist *rectangle,
        unsigned_word insert_upper_intervals)
{
    two_d_segment_tree_node_type
            *right_path = NULL,
            *left_path = NULL;

    while (is_tree(tree)) /* while we are not in a leaf. */
        if      (key_b < key(tree))  /* segment must be on the left sub tree */
            tree = left_node(tree);
        else if (key_a >= key(tree)) /* segment must be on the right sub tree */
            tree = right_node(tree);
        else if ((key_a < key(tree)) && (key_b > key(tree))) /* segment falls in between */
        {
            right_path = right_node(tree);
            left_path = left_node(tree);
            break ;
        }
        else if (key_a == key(tree)) /* segment is on the right but touches the node, so stop */
        {
            right_path = right_node(tree);
            break ;
        }
        else                         /* segment is on the left but touches the node, so stop */
        {
            left_path = left_node(tree);
            break ;
        }


    tree = NULL;
    if (left_path) /* check if we need to follow the left path */
    {
        while (is_tree(left_path)) /* while we are not in a leaf */
            if (key_a < key(left_path)) /* if the key is greater then to the endpoint a */
            {                           /* then the segment falls in between this interval so select right child */
                tree = right_node(left_path);
                attach_segment(tree, lower(rectangle), upper(rectangle), rectangle);
                left_path = left_node(left_path); /* go left and check if any smaller nodes interval also contain the interval 
*/
            }
            else if (key_a == key(left_path)) /* if the end point a is on the node  */
            {                                 /* insert segment but look no further */
                tree = right_node(left_path);
                attach_segment(tree, lower(rectangle), upper(rectangle), rectangle);
                break ;
            }
            else /* if the interval was not selected search for a larger node, ie go right */
                left_path = right_node(left_path);

        if (!right_node(left_path) && key_a == key(left_path)) /* check if leaf falls on endpoint a*/
            attach_segment(left_path, lower(rectangle), upper(rectangle), rectangle);

        if (insert_upper_intervals && tree)
            while ((tree = upper_node(tree)))             /* Attach all the segments all the way up to the root */
                attach_segment(tree, lower(rectangle), upper(rectangle), NULL); /* so when we build the y trees their leafs */
                                                          /* will always be able to point to a leaf on the left or right 
x-trees y-tree leaf */
    }

    tree = NULL;
    if (right_path) /* check if we need to follow the right path. */
    {
        while (is_tree(right_path)) /* while we are not in a leaf */
            if (key_b > key(right_path)) /* if key is smaller then the endpoint b*/
            {                            /* then part of the segment falls in between this interval so select left child */
                tree = left_node(right_path);
                attach_segment(tree, lower(rectangle), upper(rectangle), rectangle);
                right_path = right_node(right_path); /* check if any larger node also contain the interval */
            }
            else if (key_b == key(right_path)) /* end point falls on the key so insert and search no longer. */
            {
                tree = left_node(right_path);
                attach_segment(tree, lower(rectangle), upper(rectangle), rectangle);
                break ;
            }
            else /* we didn't insert (node > endpoint_b) so search for something smaller (go left) */
                right_path = left_node(right_path);

        if (insert_upper_intervals && tree)
            while ((tree = upper_node(tree)))             /* Attach all the segments all the way up to the root */
                attach_segment(tree, lower(rectangle), upper(rectangle), NULL); /* so when we build the y trees their leafs */
    }

}

/*  AS PRE-DEFINE BY THE ASSIGNMENT:
        Creates a 2D segment tree out of a list of rectangles.
 */
void populate_second_d_segment_tree(two_d_segment_tree_node_type *tree)
{
    /* we can either do this recursively or with a stack,
     * being that both are trivial will do this with a stack since its a tad faster :)  */
    interval_link_list_type *intervals;

    /* we have to stacks available to us, we only need one so just use stack 0 */
    #define stack 0
    reset_stack(stack);
    push(stack, tree);
    while (stack_has_element(stack))
    {
        tree = pop(stack);
        if (interval_list(tree))
        {
            set_y_axis(tree, create_balanced_tree(((rectlist *)interval_list(tree)), INTERVAL_LIST));
            intervals = interval_list(tree);

            while (intervals)
            {
                /* Fractional Cascading will insert intervals without rectangles to build the second dimension tree.
                        but without it the if statement is redundant and always true,
                        as such we prob won't get any misses on the branch predictor ... but its a tad faster this way. */
                #ifdef ENABLE_FRACTIONAL_CASCADING
                if (rectangle(intervals))
                #endif
                    insert_segment(
                        y_axis(tree),
                        lower(rectangle(intervals)),
                        upper(rectangle(intervals)),
                        rectangle(intervals),
                        DO_NOT_INSERT_INTO_PARENTS
                    );
                intervals = prev_interval(intervals);
            }
        }

        if (is_tree(tree)) /* its not a leaf so push both nodes */
        {
            push(stack, right_node(tree));
            push(stack, left_node(tree));
        }
    }
    #undef stack
}


two_d_segment_tree_node_type *find_node(two_d_segment_tree_node_type *tree, key_type key)
{
    if (!tree)
        return NULL;

    while (is_tree(tree))
        if (key < key(tree))
            tree = left_node(tree);
        else
            tree = right_node(tree);

    return tree;
}


/*
    Applies a fractional cascading technique to the 2D segment tree, allowing (log n) queries
    instead of (log n)**2
    Basically we reduce the query times by chaining all the second dimensional trees by their leaves
    and using a parent node that only contains nodes with intervals we simply jump from tree to tree
     going up to the root allocating all the nodes.
 */
void apply_fractional_cascading(two_d_segment_tree_node_type *tree)
{
    two_d_segment_tree_node_type
            *x_node,
            *temp;

    /* we need 2 stacks, one for traversing the first coordinate and the other for the second coordinate */
    #define x_stack 0
    #define y_stack 1

    reset_stack(x_stack);
    push(x_stack, tree);

    while (stack_has_element(x_stack))
    {
        tree = pop(x_stack);
        x_node = tree;

        if (is_tree(tree)) /* push the child nodes while we have the chance. */
        {
            push(x_stack, right_node(tree));
            push(x_stack, left_node(tree));
        }

        reset_stack(y_stack); /* reset the y stack to start linking  */
        if (y_axis(tree))
            push(y_stack, y_axis(tree));

        while (stack_has_element(y_stack)) /* while we still have nodes to evaluate. */
        {
            tree = pop(y_stack);

            if (is_tree(tree))
            {
                push(y_stack, right_node(tree));
                push(y_stack, left_node(tree));
            }
            else /* we are a leaf on the y tree. */
            {
                /* we'll attach a new object whose left pointer will point to the leaf on the x cord left node and right node
                   unless we are at x-cord leaf than just leave it as NULL */

                set_object(tree, get_new_empty_tree());

                if (is_tree(x_node)) /* check that the x node has a left and right child. */
                {                     /* connect this leaf with the leafs of the x_nodes left and right appropriate leave. */
                    set_right_node(
                        object(tree),
                        find_node(
                            y_axis(right_node(x_node)),
                            key(tree)));

                    set_left_node(
                        object(tree),
                        find_node(
                            y_axis(left_node(x_node)),
                            key(tree)));
                }

                /* go up to root through parent skipping all nodes who don't contain any intervals*/
                while (tree && upper_node(tree)) /* while we are not at the root of the y tree. */
                    if (interval_list(upper_node(tree))) /* if the upper already has intervals ok, just go up */
                        tree = upper_node(tree);
                    else /* if the upper doesn't intervals we need to find a higher one that does or set it to NULL */
                    {
                        temp = tree; /* save current leaf */
                        while ((tree = upper_node(tree)) && !interval_list(tree)); /* keep going up until
                                                        we hit one that does have intervals or we hit NULL. */
                        set_upper_node(temp, tree);
                    }
            }

        }
    }
    #undef x_stack
    #undef y_stack
}

typedef two_d_segment_tree_node_type stree_t;
stree_t *create_2dstree(rectlist *data)
{
    stree_t *tree = create_balanced_tree(data, RECTANGLE_LIST); /* create balanced tree along the x-axis */
    #undef RECTANGLE_LIST
    #undef INTERVAL_LIST

    while (data) /* Insert all the segments along x-axis */
    {
        /* If have enable fractional cascading we have to insert the keys for the second coordinate tree
            not only in their original place but every other tree on top of it ...                          */
            insert_segment(tree, left(data), right(data), data,
                #ifdef ENABLE_FRACTIONAL_CASCADING
                    INSERT_INTO_PARENTS
                #else
                    DO_NOT_INSERT_INTO_PARENTS
                #endif
                );
        data = next_rectangle(data);
    }

    /* create a segment tree on each node appropriately, along the second axis. */
    populate_second_d_segment_tree(tree);

    #ifdef  ENABLE_FRACTIONAL_CASCADING
        apply_fractional_cascading(tree);
    #endif

    return tree;
}
#undef INSERT_INTO_PARENTS
#undef DO_NOT_INSERT_INTO_PARENT

rectlist *fractional_cascading_query(stree_t *tree, int x, int y)
{
    /*
       With Fractional cascading we search for the initial leaf and jump from leaf to leaf,
       depending on the x-coordinate, at each leaf we go up to the root adding all the intervals we find.
    */

    interval_link_list_type
            *intervals = NULL;

    rectlist
            *results = NULL, /* store results as new link list of rectangles. */
            *temp = NULL;

    stree_t
            *y_axis = NULL;

    two_d_segment_tree_node_type
            *x_node = tree;

    y_axis = y_axis(tree);

    /*
       Locate initial leave.
    */
    while (is_tree(y_axis)) /* if there is a y-axis segment tree search along it  */
    {
        if (y < key(y_axis))
            y_axis = left_node(y_axis);
        else
            y_axis = right_node(y_axis);

        intervals = interval_list(y_axis);
        while (intervals) /* copy all intervals it finds */
        {
            temp = malloc(sizeof(rectlist));
            memcpy(temp, rectangle(intervals), sizeof(rectlist));
            set_next_rectangle(temp, results); // save previous results ...
            results = temp;

            intervals = prev_interval(intervals);
        }
    }

    /* y_axis is now a leaf ... */
    tree = y_axis;
    while (is_tree(x_node))
    {
        if (x < key(x_node))
        {
            tree = y_axis = left_node(object(tree));
            x_node = left_node(x_node);
        }
        else
        {
            tree = y_axis = right_node(object(tree));
            x_node = right_node(x_node);
        }


        /* go up to the root and copy all intervals found. */
        while (y_axis)
        {
            intervals = interval_list(y_axis);
            while (intervals) /* copy all intervals it finds */
            {
                temp = malloc(sizeof(rectlist));
                memcpy(temp, rectangle(intervals), sizeof(rectlist));
                set_next_rectangle(temp, results); // save previous results ...
                results = temp;

                intervals = prev_interval(intervals);
            }

            y_axis = upper_node(y_axis);
        }
    }

    return results;
}

/*
    AS PRE-DEFINE BY THE ASSIGNMENT:

    returns the list of all rectangles that contain the point (x,y)
 */
rectlist *query_2dstree(stree_t *tree, int x, int y)
{
    #ifdef ENABLE_FRACTIONAL_CASCADING
        return fractional_cascading_query(tree, x, y);
    #else
    interval_link_list_type
            *intervals = NULL;
    rectlist
            *results = NULL, /* store results as new link list of rectangles. */
             *temp = NULL;
    stree_t
            *y_axis = NULL;
    /*
        To search we simply search each node along the x-axis, if any of them
        contain the interval and the interval is contain within the nodes interval
        then search along the y-axis.
     */
    while (is_tree(tree))
    {
        if (x < key(tree))
            tree = left_node(tree);
        else
            tree = right_node(tree);

        y_axis = y_axis(tree);
        while (y_axis && is_tree(y_axis)) /* if there is a y-axis segment tree search along it  */
        {
            if (y < key(y_axis))
                y_axis = left_node(y_axis);
            else
                y_axis = right_node(y_axis);

            intervals = interval_list(y_axis);
            while (intervals) /* copy all intervals it finds */
            {
                temp = malloc(sizeof(rectlist));
                memcpy(temp, rectangle(intervals), sizeof(rectlist));
                set_next_rectangle(temp, results); // save previous results ...
                results = temp;

                intervals = prev_interval(intervals);
            }
        }
    }

    return results;
    #endif
}


int main()
{  int i, j;
    struct rectlist *rect = malloc(sizeof(rectlist) * 1000100);
    struct rectlist *start, *tmp;

    stree_t * s;
    printf("starting \n");
    for(i = 0; i < 1000; i++)
    { for ( j= 0; j< 1000; j++)
    {   (rect[1000*i+j]).left = 10*i;
        (rect[1000*i+j]).right = 10*i + 40;
        (rect[1000*i+j]).lower = 10*j;
        (rect[1000*i+j]).upper = 10*j+5;
    }
    }
    for(i = 0; i<1000099; i++)
    {  (rect[i]).next = rect+(i+1);
    }
    (rect[1000099]).next = NULL;
    for(i=1000000; i<1000050; i++)
    {   (rect[i]).left =  100 + 10*(i-1000000);
        (rect[i]).right = 200000;
        (rect[i]).lower = 100;
        (rect[i]).upper = 110 + 10*(i-1000000);
    }
    for(i=1000050; i<1000090; i++)
    {   (rect[i]).left =  100;
        (rect[i]).right = 120;
        (rect[i]).lower = 100 + 100*(i-1000050);
        (rect[i]).upper = 200 + 100*(i-1000050);
    }
    for(i=1000090; i<1000100; i++)
    {   (rect[i]).left = 5000 + (i-1000090);
        (rect[i]).right = 10000 - (i-1000090);
        (rect[i]).lower = 5000 + (i-1000090);
        (rect[i]).upper = 10000 - (i-1000090);
    }
    start = tmp = rect;
    i=0;
    while(tmp != NULL)
    {  i++;  tmp = tmp->next; }
    printf("Made %d rectangles\n", i);

    s = create_2dstree(start);
    
    for(i = 0; i < 5; i++)
    { for ( j= 0; j< 1000; j++)
    {  if((start=query_2dstree(s,10*i+3, 10*j+7)) != NULL )
    {  printf("Error at position %d, %d\n", 10*i+3, 10*j+7);
        printf("First rectangle in answer left %d, right %d, lower %d, upper %d\n",
                start->left, start->right, start->lower, start->upper);
        exit(-1);
    }
    }
    }
    for(i = 5; i < 8; i++)
    { for ( j= 0; j< 700; j++)
    {  int leftsum = 0;
        start= tmp= query_2dstree(s,10*i+3, 10*j+2);
        if( start == NULL )
        {  printf("Error at position %d, %d: no rectangle found\n", 10*i+3, 10*j+2);
            exit(-1);
        }

        while( tmp != NULL )
        {  if( (tmp->lower != 10*j) || (tmp->upper != 10*j+5) )
        {  printf("Error at position %d, %d\n", 10*i+3, 10*j+2);
            printf("Answer left %d, right %d, lower %d, upper %d\n",
                    tmp->left, tmp->right, tmp->lower, tmp->upper);
            exit(-1);
        }
            leftsum += tmp->left;
            tmp = tmp->next;
        }
        if( leftsum != (140 + 40*(i-5)) )
        {  printf("Error at position %d, %d\n", 10*i+3, 10*j+2);
            printf("leftsum is %d, should be %d\n", leftsum, 140+40*(i-5) );
            printf("answer rectangles left boundaries are\n");
            while(start != NULL )
            {  printf("%d, ", start->left);
                start=start->next;
            }
            printf("\n");
            exit(-1);
        }
    }
    }

    printf("End of tests\n");
    return 0;
}

