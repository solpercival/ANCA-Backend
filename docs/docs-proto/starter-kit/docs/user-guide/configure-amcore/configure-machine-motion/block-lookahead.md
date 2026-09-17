# Block lookahead

When executing a block of code (i.e. a line of a part program), the CNC can take into account the following lines of code as well in order to improve the performance. This feature to process the part program blocks ahead of time is called lookahead.

To better understand lookahead, consider a scenario where you are driving on a road. If the visibility is poor, you will have to drive slowly since it is not clear what is ahead of you. On the contrary if you can see a long distance ahead, you can drive faster. Similarly, without lookahead the CNC will have to stop at the end of every move. With lookahead, the CNC can maintain a higher feedrate and achieve a shorter cycle time.

The size of the lookahead buffer is specified by [Lookahead buffer size parameter](../../reference/parameter-reference.md#motion-control) (`vel_look_max`). This feature is particularly useful when moves are small. When small moves are commanded in the part program, if lookahead buffer size is not big enough, the machine may not be able to achieve the programmed feedrate.

The value specified for the lookahead buffer size parameter, determines the number of blocks to consider when controlling the feedrate. These blocks can be moves or non-move blocks. Lookahead buffer size can be set to any value from 1 to 200. However, the maximum number of move blocks that the CNC can process is 100. Therefore if the part program is consisted of only move blocks, setting the lookahead buffer size to a value greater than 100 will have the same effect of setting it to 100.