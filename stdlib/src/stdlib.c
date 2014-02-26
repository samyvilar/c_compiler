

#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <stdio.h>

#define word_type unsigned long long int

typedef struct block_type {
    struct block_type
        *_next,  // to be used by the pools (small and large)
        *_prev_free_block, // to be used to keep track of all blocks sorted in descending order by address ...
        *_next_free_block;
    word_type _length;
} block_type;
#define next_block(block) (*(block_type **)(block))
#define set_next_block(block, value) (next_block(block) = (value))
#define next_free_block(block) ((block)->_next_free_block)
#define set_next_free_block(block, value) (next_free_block(block) = (value))
#define prev_free_block(block) ((block)->_prev_free_block)
#define set_prev_free_block(block, value) (prev_free_block(block) = (value))
#define block_length(block) ((block)->_length)
#define set_block_length(block, value) (block_length(block) = (value))



#define NUMBER_OF_POOLS 256
block_type
    *recycled_small_blocks[NUMBER_OF_POOLS] = {NULL},
    *recycled_large_blocks = NULL,  // Anything that's bigger than a page 4096 bytes (page)
    *recycled_blocks = NULL;

#define BLOCK_SIZE 32
#if ((BLOCK_SIZE - 1) & BLOCK_SIZE)
    #error "BLOCK_SIZE must be a power of 2"
#endif

void free(void *);

#define initialize_block(block, blk_len) \
    set_block_length(block, blk_len), \
    set_next_block(block, block),\
    set_next_free_block(block, NULL), \
    set_prev_free_block(block, NULL)

//#define SAFE_MODE

#define is_null(ptr) (!(ptr))
#define is_not_null(ptr) (ptr)

void detach_recycled_block(block_type *block)
{
    if (is_not_null(next_free_block(block)))  // if it has next block update it so it points to previous ..
        set_prev_free_block(next_free_block(block), prev_free_block(block));

    if (is_not_null(prev_free_block(block))) // if it has a previous block update it so it points to next ..
        set_next_free_block(prev_free_block(block), next_free_block(block));

    if (block == recycled_blocks) // if block is initial update recycled blocks ...
    {
        recycled_blocks = next_free_block(block);
        #ifdef SAFE_MODE
            if (recycled_blocks && is_not_null(prev_free_block(recycled_blocks)))
                printf("NULL expected!\n"), exit(-1);
        #endif
    }
}


void *malloc(size_t amount)
{
    word_type blk_len = 1 + ((amount + (BLOCK_SIZE - (amount & (BLOCK_SIZE - 1)))) / BLOCK_SIZE);
    block_type *block;
    if ((blk_len < NUMBER_OF_POOLS) && is_not_null(block = recycled_small_blocks[blk_len]))  // get a small block
        detach_recycled_block(block), recycled_small_blocks[blk_len] = next_block(block);
    else if (is_not_null(block = recycled_large_blocks) && (blk_len <= block_length(block))) // get a large block ...
    {
        detach_recycled_block(block), recycled_large_blocks = next_block(block);  // remove it
        if (blk_len != block_length(block))  // create and recycle any of the remaining block(s) ...
            initialize_block(block + blk_len, block_length(block) - blk_len), free(block + blk_len);
    }
    else  // TODO: see if we can merge large sequential blocks to serve request ...
        block = sbrk(blk_len * BLOCK_SIZE);  // allocate a new sequence of bytes ...

    initialize_block(block, blk_len);
    return ((void *)block) + sizeof(block_type);
}


void de_fragment(block_type *block)  // recycled blocks are inserted in descending order by the blocks address ...
{
    if (block > recycled_blocks) // if recycled_blocks is either NULL or block has an address greater than recycled_blocks
    {
        set_prev_free_block(block, NULL), set_next_free_block(block, recycled_blocks);
        if (is_not_null(recycled_blocks))  // if recycle_nodes is not NULL update it so it points to block ..
            set_prev_free_block(recycled_blocks, block);
        recycled_blocks = block; // set block as the first recycled element ...
    }
    else
    {
        block_type *blocks = recycled_blocks;
        while (block < next_free_block(blocks)) // search for the largest address or NULL
            blocks = next_free_block(blocks);

        set_next_free_block(block, next_free_block(blocks));
        if (is_not_null(next_free_block(blocks)))
            set_prev_free_block(next_free_block(blocks), block);
        set_next_free_block(blocks, block), set_prev_free_block(block, blocks);
    }

    word_type blk_len;
    while (is_not_null(recycled_blocks) && (sbrk(0) == (recycled_blocks + block_length(recycled_blocks))))
    {   // we have at least 1 recycled block check if its at the end of heap ...
        blk_len = block_length(recycled_blocks);

        if (recycled_blocks == recycled_large_blocks)
            recycled_large_blocks = next_block(recycled_blocks);
        else if ((blk_len < NUMBER_OF_POOLS) && (recycled_blocks == recycled_small_blocks[blk_len]))
            recycled_small_blocks[blk_len] = next_block(recycled_blocks);
        else
        {
            block = (blk_len < NUMBER_OF_POOLS) ? recycled_small_blocks[blk_len] : recycled_large_blocks;

            while (recycled_blocks != next_block(block))
            #ifdef SAFE_MODE
                if (is_null(next_block(block)))
                    printf("corrupt memory block ...\n"), exit(-3);
                else
                    block = next_block(block);
            #else
                block = next_block(block);
            #endif

            set_next_block(block, next_block(block));
        }

        if (brk(recycled_blocks))  // shrink the heap ...
            printf("error resetting brk %p\n", brk(block)), exit(-3);
        detach_recycled_block(recycled_blocks);
    }
}


void free(void *addr)
{
    if (is_null(addr) || ((addr -= sizeof(block_type)) && (next_block((block_type *)addr) != addr)))
    #ifdef SAFE_MODE
        printf("freeing invalid memory %p\n", addr), exit(-2);
    #else
        return ;
    #endif

    #define block ((block_type *)addr)
    word_type blk_length = block_length(block);

    if (blk_length < NUMBER_OF_POOLS)
        set_next_block(block, recycled_small_blocks[blk_length]), (recycled_small_blocks[blk_length] = block);
    else if (is_not_null(recycled_large_blocks) && (block_length(recycled_large_blocks) > block_length(block)))
    {
        block_type *large_blocks = recycled_large_blocks;  // sort large blocks in descending order by block length ...
        while (next_block(large_blocks) && (block_length(next_block(large_blocks)) > blk_length))
            large_blocks = next_block(large_blocks);
        set_next_block(block, next_block(large_blocks)), set_next_block(large_blocks, block);
    }
    else // otherwise empty or first block ...
        set_next_block(block, recycled_large_blocks), (recycled_large_blocks = block);

    de_fragment(block);
    #undef block
}



#define RAND_GEN_STATE_LENGTH 624U
unsigned int
    _mt_state[RAND_GEN_STATE_LENGTH] = {  // MERSENNE TWISTER initial state ...
		1212423U, 1644249540U, 1058299835U, 1281480650U, 161662491U, 3086588844U, 3549202860U, 1139407122U, 3575607175U, 2763039517U, 181727813U, 4153246276U, 3917309199U, 216025545U, 3967331675U, 3184032711U, 2830647753U, 2624886824U, 9732772U, 1996312263U, 813828658U, 438355919U, 2760219585U, 4016492294U, 1031559697U, 1891213774U, 2440928709U, 3832528542U, 1600338189U, 1526787545U, 126774870U, 2157415949U, 221909771U, 1969710712U, 2163289823U, 1967571540U, 1329408173U, 2862159873U, 676664405U, 3687154352U, 2126732231U, 2577017671U, 1709047651U, 1374630869U, 820504272U, 1974689853U, 1609110490U, 2173831318U, 4047541908U, 2436053188U, 3355532368U,
		758568946U, 802272430U, 1882154715U, 1756642872U, 2214071732U, 4163751686U, 855595570U, 1432442868U, 2334970084U, 2730721530U, 4260272661U, 1580372204U, 738001600U, 3565868544U, 1164118640U, 1438685143U, 1427598769U, 1539405492U, 1456321198U, 177219153U, 2274850620U, 4165220798U, 3321621722U, 4094923495U, 4187027519U, 615386104U, 2430234917U, 2563605425U, 1651818734U, 1842939291U, 2580848659U, 117653511U, 901579286U, 2957613314U, 518675797U, 129781727U, 388160082U, 1473512626U, 3255739896U, 3564621665U, 4109255685U, 2291272890U, 58031349U, 65825287U, 3946091554U, 3890944613U, 296485023U, 495605277U, 1182039764U, 2007566189U,
		1855764993U, 2573165158U, 1862620635U, 4177693034U, 2808637398U, 848128782U, 1970780913U, 3352768796U, 1829304488U, 3929771035U, 1008672231U, 2761452435U, 2661943718U, 196776486U, 2145124209U, 1770960804U, 2803417486U, 2267826354U, 1143922151U, 344433206U, 3872122311U, 616794830U, 3658482113U, 2106557446U, 3883390528U, 2479252461U, 139023562U, 215256626U, 3411205179U, 890428058U, 4188186949U, 2997698338U, 1862404133U, 1260681914U, 1781497678U, 520585651U, 1380185896U, 3795088567U, 1913806735U, 1531228562U, 2754001548U, 2130679956U, 3952210008U, 11634551U, 801776004U, 2706038182U, 4070716999U, 3034959208U, 2944255335U, 2365910639U,
		3347408536U, 1304915647U, 2569297807U, 4216793147U, 2272319155U, 1564503409U, 2198609357U, 1415875145U, 1101207303U, 1439976446U, 560362300U, 2008716110U, 1889166798U, 705622607U, 2344280272U, 3771274624U, 644716630U, 1109205142U, 1141877564U, 2810000571U, 2460733096U, 772244414U, 4037650595U, 3666683854U, 1452829072U, 3382132709U, 1093160047U, 3301901848U, 4272872538U, 2706870481U, 2110918388U, 3532915807U, 960427267U, 1040860647U, 1455895516U, 2120465387U, 407854605U, 520098013U, 4128763118U, 1538674495U, 302477877U, 2491509929U, 4142162744U, 1003665929U, 1106327376U, 3388746937U, 1434660903U, 1250973124U, 490423424U, 529172296U,
		2802116657U, 1654122473U, 1751230291U, 2622481958U, 3903525121U, 2795882648U, 3958935441U, 2732836714U, 2104251609U, 3876393482U, 1896738656U, 2269207321U, 944203132U, 2145281730U, 2333206214U, 1911222316U, 963893146U, 2253093532U, 1656221489U, 736235212U, 3249472345U, 575503712U, 3997882303U, 1193196044U, 319511810U, 4216308908U, 193151214U, 4144626890U, 2226605362U, 3505398998U, 3494348272U, 2693522631U, 2449584034U, 3473337098U, 2596375672U, 4057970446U, 2744397326U, 678336426U, 7459073U, 952631125U, 1172257402U, 2226841209U, 2490483322U, 1664873036U, 1466748502U, 280688713U, 1050805956U, 1256689740U, 3887080538U, 912324887U,
		3710948878U, 3671271709U, 505563091U, 918241853U, 1509869584U, 2131560629U, 1186513925U, 3555162774U, 2969574092U, 2265240138U, 4184309613U, 2903057772U, 2544214893U, 3302548179U, 2929904921U, 96165809U, 3539565280U, 3748001691U, 2581792773U, 1645144785U, 3611030815U, 2224533788U, 4252233703U, 3378162182U, 3085222412U, 796659354U, 2113416663U, 206281860U, 1211327787U, 2039506090U, 545536912U, 4177236202U, 506191368U, 3545817668U, 387597856U, 2546256830U, 332398155U, 3090315191U, 1340872842U, 823464697U, 893828704U, 2506784004U, 3809839747U, 3894289830U, 1502423104U, 1694673869U, 177337509U, 2483344195U, 767304400U, 1837829436U,
		3130842942U, 4261359578U, 2704802508U, 2419808886U, 335463669U, 4187869915U, 3573663851U, 1489746492U, 3803586630U, 3875711343U, 3266028755U, 3936048968U, 3087897808U, 2344491540U, 3700429289U, 1406356622U, 2453585064U, 643656272U, 3371156175U, 4184541116U, 2023245468U, 1009312307U, 1351846498U, 1274647891U, 933153951U, 2575356673U, 2312428662U, 1109462796U, 2910053994U, 2715783250U, 866042075U, 4241771187U, 2794039485U, 2429995945U, 3446267590U, 3865006601U, 1556658499U, 4012075612U, 1233047502U, 3739665663U, 593138881U, 3919510139U, 3104508591U, 818728089U, 4269382326U, 280487875U, 2649410634U, 3941409220U, 1997722592U, 3304587811U,
		4259051519U, 4150440908U, 2866002188U, 2868019688U, 2123988149U, 1865844840U, 375587794U, 2228872512U, 578143857U, 3099641085U, 74658052U, 1841921022U, 466772998U, 3585256906U, 2063475386U, 1576454197U, 2364330483U, 3210727045U, 1610857396U, 1591733467U, 3054443893U, 3975958631U, 3914153193U, 3279438792U, 4182205326U, 3259743513U, 1405781691U, 2551624412U, 2998886673U, 2616817915U, 1710816442U, 1201195589U, 996291155U, 1592870719U, 2936228599U, 941404459U, 2051992186U, 3388692235U, 4076117933U, 2310610732U, 2851794093U, 2775714195U, 3155386558U, 2274215862U, 3233488783U, 445210568U, 4209824629U, 1288934684U, 3658570496U, 329417919U,
		3982596076U, 3713587677U, 2109195305U, 781307228U, 3555738337U, 1573082816U, 1388676284U, 3105981737U, 3265957520U, 4254854297U, 4032349277U, 1521338546U, 3353148220U, 2405226617U, 249052454U, 1209235358U, 873155164U, 1807979502U, 232605166U, 876279434U, 519643159U, 521599417U, 1875085476U, 348665793U, 1260079566U, 2498553685U, 2426787326U, 4208282136U, 2240524628U, 2472410780U, 262800389U, 1650279593U, 2032271353U, 2620241546U, 1919929691U, 2423730230U, 155048505U, 3267271475U, 1418718119U, 3681407030U, 1681032098U, 3990170633U, 1441905581U, 4152498328U, 1438362084U, 2184746519U, 2671211784U, 3922299058U, 2139138198U, 2015122517U,
		1251621607U, 2628277378U, 857856069U, 1325023743U, 201259261U, 3116540569U, 1225530352U, 3159490783U, 1893441020U, 471645085U, 3574074302U, 1755301983U, 3956694245U, 1435745934U, 1580054332U, 1573122531U, 3488506365U, 1903139082U, 1295730220U, 405522071U, 414001770U, 1223325610U, 2822290256U, 1910426420U, 303598276U, 3243091248U, 3647961596U, 1530763897U, 3493866295U, 2665210212U, 2317976863U, 2590575443U, 2646004184U, 3294918374U, 461797182U, 1016019804U, 4207585587U, 1188000216U, 2629045638U, 1021377278U, 1879504417U, 659963020U, 1665192233U, 1889070774U, 4279705378U, 3383685877U, 2663744255U, 2817594563U, 1132428056U, 3285906385U,
		3030095311U, 422039767U, 2774103498U, 3033235936U, 570044963U, 1870628041U, 1020685539U, 2131980939U, 3837660271U, 3667178650U, 1300243292U, 1510324913U, 4026194289U, 4134784508U, 1793506974U, 4083502527U, 2914339121U, 286731813U, 81396640U, 794038312U, 4192717265U, 3224503268U, 656616238U, 3644696882U, 20314978U, 2508300728U, 1070029425U, 4263782821U, 3390588559U, 3072901966U, 2058140431U, 3684846746U, 641014642U, 1455544336U, 194140620U, 1734318996U, 269361378U, 593096004U, 1062207983U, 2904730727U, 800264950U, 4085654316U, 2802387626U, 3890028136U, 3362866520U, 4232778249U, 1821080085U, 1038606344U, 60271949U, 3484456583U,
		1054083131U, 1605096559U, 3933974415U, 2425499750U, 3360595359U, 950054072U, 2900008645U, 2091525553U, 2233208991U, 960599329U, 2945810742U, 3230453686U, 1554567580U, 3725769253U, 3255552307U, 2644578854U, 306015851U, 994104687U, 3168116228U, 2885849240U, 681277693U, 1140925197U, 1971864057U, 3084370198U, 3053380387U, 1459832645U, 3091891221U, 3870781013U, 2093256753U, 2617677108U, 4042049171U, 4053625110U, 1273607312U, 550295677U, 941052058U, 3347790092U, 517966902U, 1840593306U, 999337844U, 2854637330U, 2329723807U, 2199073857U, 2942335936U, 228173788U, 4286052383U, 2531254624U, 3617546239U, 1277344962U, 235787846U, 1460339190U,
		2099640268U, 4096949051U, 1516476275U, 829736022U, 2793242187U, 404153899U, 828560470U, 1979305550U, 857714316U, 4122790814U, 3384695892U, 2984640439U, 2676539854U, 2101257186U, 782247414U, 3946422902U, 1927329682U, 2649430633U, 4224823714U, 1496399857U, 2335550493U, 1847755177U, 1452806583U
    },
    _mt_index = 0;

#define is_odd(value) (value & 1)
void generate_numbers()
{
    unsigned long long int index = -1, y;
    while (index++ < RAND_GEN_STATE_LENGTH)
    {
        y = (_mt_state[index] & 0x80000000) + (_mt_state[((index + 1) % RAND_GEN_STATE_LENGTH)] & 0x7fffffff);
        _mt_state[index] = _mt_state[((index + 397) % RAND_GEN_STATE_LENGTH)] ^ (y >> 1);
        if (is_odd(y))
            _mt_state[index] ^= 2567483615U;
    }
}

void srand(unsigned int seed)
{
    _mt_index = 0;
    _mt_state[0] = seed;
    unsigned long long int index = 0;
    while (index++ < RAND_GEN_STATE_LENGTH)
        _mt_state[index] = 1812433253U * (_mt_state[index - 1] ^ (_mt_state[index - 1] >> 30)) + index;
}



unsigned int rand()
{
    if (!_mt_index)
        generate_numbers();

    unsigned int y = _mt_state[_mt_index];
    y ^= (y >> 11);
    y ^= ((y << 7) & 2636928640U);
    y ^= ((y << 15) & 4022730752U);
    y ^= (y >> 18);

    _mt_index = (_mt_index + 1) % RAND_GEN_STATE_LENGTH;
    return y;
}
