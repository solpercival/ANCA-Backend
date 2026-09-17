# Functions

This section provides a comprehensive reference for all functions available in EPPL. Functions are listed in alphabetical order and include mathematical functions, string manipulation, file I/O, CNC control commands, and other callable operations.

---


### `abs`

Returns the absolute value of an integer expression.

**Syntax:**

```
integer abs(integer expr)
```

**Description:**

Return the absolute value of the argument **expr**. This function is only for obtaining the absolute value of **integer** expressions. To obtain the absolute value of a float expression, use `fabs()`.

**Parameters:**

| Parameter | Type    | Description                              |
| --------- | ------- | ---------------------------------------- |
| expr      | integer | The integer expression to evaluate       |

**Returns:**

| Type    | Description                              |
| ------- | ---------------------------------------- |
| integer | The absolute value of the expression     |

**Example:**

```
abs(-30)
```

Returns 30.

**See Also:** `fabs`

### `acos`

Returns the inverse cosine of an expression.

**Syntax:**

```
float acos(float expr)
```

**Description:**

Return the inverse cosine of the expression **expr**. **expr** must be within the range -1.0 to 1.0 inclusive. The returned value will be in **degrees** and will lie within the range 0° to 180° inclusive.

**Parameters:**

| Parameter | Type  | Description                              |
| --------- | ----- | ---------------------------------------- |
| expr      | float | The value to evaluate (range -1.0 to 1.0)|

**Returns:**

| Type  | Description                              |
| ----- | ---------------------------------------- |
| float | The inverse cosine in degrees (0° to 180°)|

**Example:**

```
acos(0.7)
```

Returns 45.573.

**See Also:** `cos`, `asin`, `atan`, `dtor`, `rtod`

### `acosh`

Returns the inverse hyperbolic cosine of an expression.

**Syntax:**

```
float acosh(float expr)
```

**Description:**

Return the inverse hyperbolic cosine of the expression **expr**.

**Parameters:**

| Parameter | Type  | Description                              |
| --------- | ----- | ---------------------------------------- |
| expr      | float | The value to evaluate                    |

**Returns:**

| Type  | Description                              |
| ----- | ---------------------------------------- |
| float | The inverse hyperbolic cosine            |

**Example:**

```
acosh(1.3)
```

Returns 0.7564.

**See Also:** `cosh`, `asinh`, `atanh`, `dtor`, `rtod`

### `alarm_load`

Loads one or more alarms from a configuration file.

**Syntax:**

```
alarm_load(string configuration_file_path)
```

**Description:**

Load one or more alarms from the specified configuration file.

Any resource files that are in the same folder as the configuration file, and have the same base file name, will also be loaded. However, resources will only be loaded for the alarm numbers listed in the configuration file; if a resource file contains resources for other alarms, those resources will be ignored.

Note that each alarm may only be loaded once, and its configuration and resources cannot subsequently be changed. If an attempt is made to load any existing alarm(s) with different configuration and/or different resources, the entire configuration file (and resource files) will be ignored and an execution error will be displayed. (Loading existing alarm(s) with the same configuration and same resources has no effect, but this will succeed.)

**Parameters:**

| Parameter                | Type   | Description                              |
| ------------------------ | ------ | ---------------------------------------- |
| configuration_file_path  | string | The configuration file path. A relative file path will be resolved relative to the OemPATH registry key, and any environment variables will be expanded. |

**Example:**

```
alarm_load("alarms/custom_alarms.cfg")
```

Loads alarms from the specified configuration file.

**See Also:** `alarm_trigger`, `alarm_severity_debug`, `alarm_severity_info`, `alarm_severity_warn`, `alarm_severity_error`, `alarm_severity_fatal`

### `alarm_trigger`

Triggers a defined transient alarm.

**Syntax:**

```
alarm_trigger(integer severity, string alarm_number)
alarm_trigger(integer severity, string alarm_number, string arg_format, ...)
```

**Description:**

Trigger a defined transient alarm.

This creates a new alarm instance, even if there are existing alarm instances for this alarm number.

Note that the specified alarm number must be configured as a transient alarm. This is an alarm representing an issue that occurs at a single instant in time, e.g. an exception has occurred.

**Parameters:**

| Parameter    | Type    | Description                              |
| ------------ | ------- | ---------------------------------------- |
| severity     | integer | The alarm severity. Valid values range from 1 to 1000. Use standard severity constants: `alarm_severity_debug` (1), `alarm_severity_info` (167), `alarm_severity_warn` (500), `alarm_severity_error` (833), and `alarm_severity_fatal` (1000). |
| alarm_number | string  | The number of the alarm to trigger.      |
| arg_format   | string  | (Optional) A string containing conversion specifiers for formatting variables. Note that the character specifier ("%c") is not supported. |
| ...          |         | (Optional) Arguments corresponding to conversion specifiers in the format string. |

**Example:**

```
alarm_trigger(alarm_severity_error, "ALRM001")
```

Triggers a transient alarm with error severity.

```
alarm_trigger(600, "ALRM002", "%s%s%d", "foo", "bar", 123)
```

Triggers a transient alarm with a severity of 600 and formatted arguments.

**See Also:** `alarm_load`, `alarm_severity_debug`, `alarm_severity_info`, `alarm_severity_warn`, `alarm_severity_error`, `alarm_severity_fatal`

### `asin`

Returns the inverse sine of an expression.

**Syntax:**

```
float asin(float expr)
```

**Description:**

Return the inverse sine of the expression **expr**. **expr** must be within the range -1.0 to 1.0 inclusive. The returned value will be in **degrees** and will lie within the range -90° to 90° inclusive.

**Parameters:**

| Parameter | Type  | Description                              |
| --------- | ----- | ---------------------------------------- |
| expr      | float | The value to evaluate (range -1.0 to 1.0)|

**Returns:**

| Type  | Description                              |
| ----- | ---------------------------------------- |
| float | The inverse sine in degrees (-90° to 90°)|

**Example:**

```
asin(0.5)
```

Returns 30.0.

**See Also:** `sin`, `acos`, `atan`, `dtor`, `rtod`

### `asinh`

Returns the inverse hyperbolic sine of an expression.

**Syntax:**

```
float asinh(float expr)
```

**Description:**

Return the inverse hyperbolic sine of the expression **expr**.

**Parameters:**

| Parameter | Type  | Description                              |
| --------- | ----- | ---------------------------------------- |
| expr      | float | The value to evaluate                    |

**Returns:**

| Type  | Description                              |
| ----- | ---------------------------------------- |
| float | The inverse hyperbolic sine              |

**Example:**

```
asinh(1.3)
```

Returns 1.0784.

**See Also:** `sinh`, `acosh`, `atanh`, `dtor`, `rtod`

### `atan`

Returns the inverse tangent of an expression.

**Syntax:**

```
float atan(float expr)
```

**Description:**

Return the inverse tangent of the expression expr. The returned value will be in degrees and will lie within the range -90 to 90.

**Parameters:**

| Parameter | Type  | Description                                       |
| --------- | ----- | ------------------------------------------------- |
| expr      | float | The expression whose inverse tangent is returned. |

**Returns:**

| Type  | Description                                                      |
| ----- | ---------------------------------------------------------------- |
| float | The inverse tangent of expr, in degrees, in the range -90 to 90. |

**Additional information:**

1. To resolve an inverse tangent to all 4 quadrants and to allow accurate calculation near 90 degrees, use `atant`, the 2-argument inverse tangent.

**Example:**

```
atan(1.0)
```

Returns 45.0.

**See Also:** `tan`, `atant`, `atanh`, `dtor`, `rtod`

### `atanh`

Returns the inverse hyperbolic tangent of an expression.

**Syntax:**

```
float atanh(float expr)
```

**Description:**

Return the inverse hyperbolic tangent of the expression **expr**.

**Parameters:**

| Parameter | Type  | Description                              |
| --------- | ----- | ---------------------------------------- |
| expr      | float | The value to evaluate                    |

**Returns:**

| Type  | Description                              |
| ----- | ---------------------------------------- |
| float | The inverse hyperbolic tangent           |

**Example:**

```
atanh(0.6)
```

Returns 0.6931.

**See Also:** `tanh`, `asinh`, `acosh`, `dtor`, `rtod`

### `atant`

Returns the inverse tangent using two arguments for full quadrant resolution.

**Syntax:**

```
float atant(float sin_expr, float cos_expr)
```

**Description:**

Return the inverse tangent of the expression **sin_expr/cos_expr**. **sin_expr** and **cos_expr** represent the sine and cosine of the angle and should both be within the range -1.0 to 1.0 inclusive. The returned value will be in **degrees** and will lie within the range -180° to 180°. This function is able to resolve the inverse tangent in 4 quadrants (unlike `atan()`).

**Parameters:**

| Parameter | Type  | Description                              |
| --------- | ----- | ---------------------------------------- |
| sin_expr  | float | Sine of the angle (range -1.0 to 1.0)    |
| cos_expr  | float | Cosine of the angle (range -1.0 to 1.0)  |

**Returns:**

| Type  | Description                              |
| ----- | ---------------------------------------- |
| float | The inverse tangent in degrees (-180° to 180°)|

**Example:**

```
atant(-0.7661, -0.6428)
```

Returns -130.0.

**See Also:** `atan`, `sin`, `cos`, `dtor`, `rtod`

### `attach`

Attaches a Part Program Processor to a Logical Machine.

**Syntax:**

```
attach lm lm_num
```

**Description:**

Attach Logical Machine is used to attach a Part Program Processor to a Logical Machine. The role of this function is to attach a logical machine.

**Parameters:**

| Parameter | Type    | Description                              |
| --------- | ------- | ---------------------------------------- |
| lm_num    | integer | The logical machine number to attach to  |

**Example:**

```
attach lm 1
```

Will cause logical machine 1 to be attached.

**See Also:** `detach`

### `axis`

Commands an axis by its axis number.

**Syntax:**

```
axis(axis_id)(position)
```

**Description:**

`axis` allows an axis to be commanded via its axis number. This is an alternative to commanding the axis via its dimension word.

**Parameters:**

| Parameter | Type    | Description                       |
| --------- | ------- | --------------------------------- |
| axis_id   | integer | The axis number to command.       |
| position  | float   | The target position for the axis. |

**Additional information:**

1. `axis` is a keyword but is disabled by default to prevent compatibility issues with existing part programs that use axis as a variable name. To enable the `axis` keyword, set the `axis_keyword.compatibility_mode` parameter to `off`.

**Example:**

```
relative
axis(1)(100)
```

Moves axis 1 by 100 units.

**See Also:** `joint`, `axismlinear`

### `axismlinear`

Moves an axis specified by an index number.

**Syntax:**

```
axismlinear axis_num, position
```

**Description:**

This type of move allows an axis to be specified by an index number rather than the normal letter name. It is intended to allow generic programs/sub-programs. For example, it is used by the Manual program to move a single axis in an analogous way to how a joint move controls a single numbered joint.

**Parameters:**

| Parameter | Type    | Description                           |
| --------- | ------- | ------------------------------------- |
| axis_num  | integer | The index number of the axis to move. |
| position  | float   | The target position for the axis.     |

**Example:**

```
axismlinear axis_num, 400.0
```

Moves the axis identified by axis_num to position 400.0.

**See Also:** `axis`, `joint`

### `axismpg`

Moves an axis under manual pulse generator (MPG) control until a stop condition is satisfied.

**Syntax:**

```
axismpg axis_num stopif variable
axismpg axis_num stopifnot variable
```

**Description:**

Commands the axis identified by axis_num to move under manual pulse generator (MPG) control. The move terminates on a boolean stop condition: with `stopif` the motion stops when variable becomes true, and with `stopifnot` the motion stops when variable becomes false. Unlike `axismlinear`, the axis is addressed by its index number rather than its letter name.

**Parameters:**

| Parameter | Type    | Description                                                                                                               |
| --------- | ------- | ------------------------------------------------------------------------------------------------------------------------- |
| axis_num  | integer | The index number of the axis to move under MPG control.                                                                   |
| variable  | boolean | The boolean stop-condition variable evaluated to terminate the move (`stopif` stops when true, `stopifnot` stops when false). |

**Example:**

```
axismpg 1 stopif (plc)bv200
```

Puts axis 1 under manual pulse generator control. The operator jogs the axis with the handwheel and the move terminates when the PLC boolean variable (plc)bv200 becomes true.

**See Also:** `jointmpg`, `axismlinear`, `axis`

### `axisswapoff`

Cancels axis swap mode.

**Syntax:**

```
axisswapoff
```

**Description:**

Cancels axis swap mode that was enabled by `axisswapon`.

**Example:**

```
axisswapoff
```

Cancels axis swap mode, returning the `Y` and `A` axes to their normal behaviour.

**See Also:** `axisswapon`

### `axisswapon`

Enables axis swap mode for 4-axis milling applications.

**Syntax:**

```
axisswapon radius
```

**Description:**

Axis swap mode is used to allow 4-axis milling applications on cylindrical sections to be programmed using Cartesian coordinates. Axis swap interchanges the `Y` and `A` axes on 4-axis mills, allowing `A` axis moves to be programmed in planar coordinates. When treating the `A` axis (a rotational axis) as the `Y` axis (a linear axis), a nominal radius must be programmed to account for the radius of the workpiece.

**Parameters:**

| Parameter | Type  | Description                                                     |
| --------- | ----- | --------------------------------------------------------------- |
| radius    | float | The nominal radius of the workpiece |

**Additional information:**

1. The variables `%xolb_axis_swapped` and `g_nominal_radius` allow the user to view the status and nominal radius of axis swap. As `axisswapon` requires an argument, using `g_nominal_radius` as the argument restores the previous nominal radius without specifying a fixed value or expression.

**Example:**

```
axisswapon 3.22
```

Causes the `Y` and `A` axes to be swapped, with a nominal radius of 3.22 units given for the `Y` axis.

**See Also:** `axisswapoff`, `g_nominal_radius`

### `barrier`

Synchronizes multiple Part Program Processors.

**Syntax:**

```
barrier(id, number_of_participants)
```

**Description:**

Waits for the specified number of PPPs to call `barrier()` with the specified ID. Allows PPPs to synchronize with one another. Should be used when using `attach`/`detach` axis commands.

**Parameters:**

| Parameter              | Type    | Description                             |
| ---------------------- | ------- | --------------------------------------- |
| id                     | integer | Identification number (1 to 2147483647) |
| number_of_participants | integer | Number of PPPs to wait for              |

**Example:**

PPP1
```
{
… do task (1)
}
barrier(1, 2)
{
… do task (3)
}
```

PPP2
```
{
… do task (2)
}
barrier(1, 2)
{
… do task (4)
}

```

PPP1 and PPP2 will be synchronised at the barrier. Tasks (3) and (4) will not be executed until both tasks (1) and (2) are completed.

**See Also:** `barrier_clear_all`, `attach`, `detach`

### `barrier_clear_all`

Clears all existing barriers.

**Syntax:**

```
barrier_clear_all()
```

**Description:**

Clears all existing barriers, which will unblock any PPPs that are waiting at barriers.

**Example:**

```
barrier_clear_all()
```

Clears all existing barriers, unblocking any PPPs that are currently waiting at a barrier.

**See Also:** `barrier`

### `bevel_head_disable`

Disables bevel head kinematics.

**Syntax:**

```
bevel_head_disable()
```

**Description:**

Disables bevel head kinematics. If bevel head kinematics is not configured in database parameters, this function will have no effect. See "configure kinematics" section in AMCore user guide for more information.

**Additional information:**

1. This function applies to Profile Cutting Control (PCC) kinematics only.

**Example:**

```
bevel_head_disable()
```

Disables bevel head kinematics.

**See Also:** `bevel_head_enable`, `bevel_head_mode`

### `bevel_head_enable`

Enables bevel head kinematics.

**Syntax:**

```
bevel_head_enable()
```

**Description:**

Enables bevel head kinematics. If bevel head kinematics is not configured in database parameters, this function will have no effect. See "configure kinematics" section in AMCore user guide for more information.

**Additional information:**

1. This function applies to Profile Cutting Control (PCC) kinematics only.

**Example:**

```
bevel_head_enable()
```

Enables bevel head kinematics.

**See Also:** `bevel_head_disable`, `bevel_head_mode`

### `bevel_head_mode`

Changes bevel head kinematics mode.

**Syntax:**

```
bevel_head_mode(integer mode)
```

**Description:**

Changes bevel head kinematics mode. Two modes are available: mode 0 and mode 1. If you select mode 0 (`bevel_head_mode(0)`), joint number 3 will be controlled and affected by bevel head kinematics. In this mode, if you rotate the bevel head, joint number 3 may move as well. If you select mode 1 (`bevel_head_mode(1)`), joint number 3 will have a simple one to one mapping with axis Z. In this mode, the rotation of the bevel head will have no effect on joint number 3. The default mode is specified by `bevel_head_mode` parameter.

**Parameters:**

| Parameter | Type    | Description                  |
| --------- | ------- | ---------------------------- |
| mode      | integer | The bevel head mode (0 or 1) |

**Additional information:**

1. This function applies to Profile Cutting Control (PCC) kinematics only.

**Example:**

```
bevel_head_mode(1)
```

Selects mode 1, giving joint number 3 a simple one to one mapping with axis Z so that rotating the bevel head has no effect on joint number 3.

**See Also:** `bevel_head_enable`, `bevel_head_disable`

### `cbrt`

Returns the cube root of an expression.

**Syntax:**

```
float cbrt(float expr)
```

**Description:**

Return the cubed root of the expression **expr**. **expr** must be >= 0. The return value will be >= 0.

**Parameters:**

| Parameter | Type  | Description                              |
| --------- | ----- | ---------------------------------------- |
| expr      | float | The value to evaluate (must be >= 0)     |

**Returns:**

| Type  | Description                              |
| ----- | ---------------------------------------- |
| float | The cube root of the expression          |

**Example:**

```
cbrt(3.0)
```

Returns 1.4422.

**See Also:** `sqrt`, `pow`

### `cc_dim_programmed`

Determines whether a dimension word is programmed for a canned cycle.

**Syntax:**

```
boolean cc_dim_programmed(integer index)
```

**Description:**

Determines whether the dimension word at the given one-based index was programmed for the current canned cycle. When a canned cycle is called, dimension words that are not explicitly stated take the values remembered from the previous call; this function reports whether a particular dimension word is currently programmed. The index must be between 1 and `dimensions_num` inclusive.

**Parameters:**

| Parameter | Type    | Description                                                           |
| --------- | ------- | --------------------------------------------------------------------- |
| index     | integer | One-based index of the dimension word to query (1 to `dimensions_num`). |

**Returns:**

| Type    | Description                                                                              |
| ------- | ---------------------------------------------------------------------------------------- |
| boolean | true if the dimension word at index is programmed for the canned cycle; false otherwise. |

**Example:**

```
if (cc_dim_programmed(1)) then
    { the first dimension word is programmed }
ifend
```

Tests whether the first dimension word (index 1) is programmed for the current canned cycle.

**See Also:** `dimensions_num`

### `centre_comp`

Enables center compensation for off-center tools.

**Syntax:**

```
centre_comp(Δy, Δz, axis_selector)
```

**Description:**

Enables runout compensation, typically used to compensate for a slightly off-centre tool (tube) on laser tube cutting machines when the centreline of the tube is not perfectly aligned with the centreline of the `A` axis.

**Parameters:**

| Parameter     | Type   | Description                                                         |
| ------------- | ------ | ------------------------------------------------------------------- |
| Δy            | float  | Distance from `A` axis centreline to tube centreline along `Y` axis |
| Δz            | float  | Distance from `A` axis centreline to tube centreline along `Z` axis |
| axis_selector | string | "Y", "Z", or "YZ" - axes for compensation                           |

**Additional information:**

1. Δy and Δz should be measured when `A` axis is at zero position (`A`=0).

**Example:**

```
G1 X0 Y100 Z100
centre_comp(5, 3, "YZ")
G1 X0 Y100 Z100
```

After running the first line, `X`, `Y` and `Z` move to (0,100,100). After the second line, compensation is activated and the user frame position changes from (0,100,100) to (0,95,97) without any real movement taking place. When the third line runs, the user frame moves from (0,95,97) back to (0,100,100), physically moving the laser head by +5 mm in the Y-direction and +3 mm in the Z-direction to its compensated position.

**See Also:** `centre_comp_cancel`, `runout_comp`

### `centre_comp_cancel`

Cancels center compensation.

**Syntax:**

```
centre_comp_cancel()
```

**Description:**

Cancels runout compensation that was activated by `centre_comp`.

**Example:**

```
centre_comp_cancel()
```

Cancels any runout compensation previously activated by `centre_comp`.

**See Also:** `centre_comp`

### `chamfer`

Inserts a chamfer at the intersection of the current move and the next move.

**Syntax:**

```
chamfer value
chamfer(expr)
```

**Description:**

A chamfer is a linear move which levels off an intersection of two moves. The value assigned to it represents how much of the two intersecting moves is to be "cut off" by the chamfer. This length is measured along both moves from the theoretical point of intersection, locating a point on each of the moves, and these points become the points between which the chamfer runs.

A chamfer is programmed by `chamfer` followed by either an expression in curved brackets or a number.

**Parameters:**

| Parameter | Type  | Description                              |
| --------- | ----- | ---------------------------------------- |
| value     | float | The chamfer length (distance from intersection point along each move) |
| expr      | float | An expression evaluating to the chamfer length |

**Additional information:**

1. 2D CRC may be applied to moves that have a chamfer modifier.
2. The following move that will be "clipped" to perform the chamfer, need not be the next block in the program. It may in fact be separated by up to 100 calculation blocks from the move with the chamfer applied.
3. If path lookahead needs to be cancelled before the next interpolation block is found, the chamfer will be ignored.
4. If one of the moves to be clipped is too short to be chamfered, the chamfer will be ignored.
5. Chamfers will always be traversed at the programmed feedrate (even if the moves being chamfered are rapid moves).
6. `chamfer` is a block modifier -- it cannot be used as a standalone statement. It must appear on a motion block.

**Example:**

```
relative
linear X23 Y31.26 chamfer(fv5)
linear X-33.4 Y2.92
```

Inserts a chamfer at the intersection with the next move. The chamfer length is given by fv5.

**See Also:** `fillet`

### `chtostr`

Converts a character code to a string.

**Syntax:**

```
string chtostr(integer number)
```

**Description:**

Returns the character (as a string of length 1) represented by the code value **number**.

**Parameters:**

| Parameter | Type    | Description                              |
| --------- | ------- | ---------------------------------------- |
| number    | integer | The character code value                 |

**Returns:**

| Type   | Description                              |
| ------ | ---------------------------------------- |
| string | A single-character string                |

**Example:**

```
new_str = chtostr(88)
```

Results in new_str having the value "X".

**See Also:** `strtoch`

### `clearlo`

Cancels live offsets for all axes or a specified axis.

**Syntax:**

```
clearlo
clearlo dimension_word
clearlo axis(axis_id)
```

**Description:**

The role of this function is to either clear all Live Offsets, or clear the Live Offset of a single Axis.

**Parameters:**

| Parameter      | Type           | Description                              |
| -------------- | -------------- | ---------------------------------------- |
| dimension_word | dimension_word | (Optional) Dimension word specifying axis |
| axis_id        | axis_id        | (Optional) Axis id specifying axis       |

**Example:**

```
clearlo
```

Will cause all live offsets to be cleared to 0.

```
clearlo W
```

Will cause the W live offset (only) to be cleared to 0.

```
clearlo axis(1)
```

Will cause the X live offset (only) to be cleared to 0.

**See Also:** `clearsa`, `eff`

### `clearsa`

Clears or presets one or more soft axis positions.

**Syntax:**

```
clearsa
clearsa dimension_word
clearsa axis(axis_id)
```

**Description:**

Clear Soft Axis is used to cancel or preset one or more soft axis positions (in user frame coordinates). The role of this function is to clear or preset one or more soft axes by taking up the soft axis position into the current machine position.

It is programmed by `clearsa` followed by one or more soft axis followed by an optional "new" value for the soft axis, representing the soft axis to be cleared and the value that it should be cleared to.

A soft axis can be specified by either dimension word or `axis` keyword.

**Parameters:**

| Parameter      | Type           | Description                              |
| -------------- | -------------- | ---------------------------------------- |
| dimension_word | dimension_word | (Optional) Dimension word(s) with optional new value |
| axis_id        | axis_id        | (Optional) Axis id specifying axis       |

**Example:**

```
clearsa U W
```

Will cause the soft axes `U` and `W` to be cleared to 0.

```
clearsa U90.0 W
```

Will cause the soft axis U to be preset to the value 90.0 and W to be cleared to 0.

**See Also:** `clearlo`

### `close`

Closes a file that was previously opened.

**Syntax:**

```
close(stream)
```

**Description:**

A disk file that has been opened by the function `open()` may be explicitly closed by the function `close()`.

**Parameters:**

| Parameter | Type   | Description                              |
| --------- | ------ | ---------------------------------------- |
| stream    | stream | A file identifier. This must be a unique name that was used in the `open()` function for this file. |

**Additional information:**

1. Before the file may be read from or written to again, it must be reopened using `open()`.
2. A file will be closed automatically when the part program is complete or is rewound or deactivated.

**Example:**

```
open(&my_file, "data", input)
:
:
close(my_file)
```

Closes the file previously opened with the identifier my_file.

**See Also:** `open`, `read`, `write`

### `cos`

Returns the cosine of an expression.

**Syntax:**

```
float cos(float expr)
```

**Description:**

Return the cosine of the expression **expr**. **expr** is assumed to be in units of **degrees**.

**Parameters:**

| Parameter | Type  | Description                              |
| --------- | ----- | ---------------------------------------- |
| expr      | float | The angle in degrees                     |

**Returns:**

| Type  | Description                              |
| ----- | ---------------------------------------- |
| float | The cosine of the angle                  |

**Example:**

```
cos(30.0)
```

Returns 0.8660.

**See Also:** `sin`, `tan`, `acos`, `dtor`, `rtod`

### `cosh`

Returns the hyperbolic cosine of an expression.

**Syntax:**

```
float cosh(float expr)
```

**Description:**

Return the hyperbolic cosine of the expression **expr**.

**Parameters:**

| Parameter | Type  | Description                              |
| --------- | ----- | ---------------------------------------- |
| expr      | float | The value to evaluate                    |

**Returns:**

| Type  | Description                              |
| ----- | ---------------------------------------- |
| float | The hyperbolic cosine                    |

**Example:**

```
cosh(0.2)
```

Returns 1.020.

**See Also:** `sinh`, `tanh`, `acosh`, `dtor`, `rtod`

### `D`

Selects a tool offset group.

**Syntax:**

```
D group_number
D(expression)
```

**Description:**

Selects a particular tool offset group from the tool table. Adjusts the tool offset transformation and sets up cutter radius compensation radius.

**Parameters:**

| Parameter    | Type       | Description                           |
| ------------ | ---------- | ------------------------------------- |
| group_number | integer    | Tool offset group number (0-99)       |
| expression   | expression | Expression evaluating to group number |

**Additional information:**

1. D-Code contains internal `sync` command.
2. Breaks program, path compensation, and velocity lookahead.
3. D0 clears all tool offsets to zero.
4. Performs the same function as `H`.

**Example:**

```
D6
tooloffset(fv3)
D0 
```

Selects tool offset group 6, then selects the group referred to by the value of fv3, and finally clears all tool offsets by selecting group 0.

**See Also:** `tooloffset`, `toolselect`, `eff`, `H`

### `db_attach`

Attaches a part program to a database file.

**Syntax:**

```
db_attach(string filename)
```

**Description:**

Attach a part program to a database file. This function is useful to part programs with simple databases that can be supported by a single database file. Subsequent database queries, menus, field entry tables and error messages are extracted from this file.

All sub part programs may access the database file registered by any of its ancestors without having to call `db_attach()`. If a sub part program calls `db_attach()` then this file is now the active database file for itself and all of its descendants.

The function performs the following operations internally:
1. Install a Master Database reference to this file with key "*pp"
2. Register the generic part program name "pp" with the Error Processor
3. Register the generic part program name "pp" with the Presentation Manager

**Parameters:**

| Parameter | Type   | Description                              |
| --------- | ------ | ---------------------------------------- |
| filename  | string | The file to be referenced for all database queries |

**Additional information:**

1. If a part program's database is too complex to be supported by a single file then it must be split into multiple files and explicit calls to `dba_put_master_entry()` and `ep_init()` must be made.
2. All ep_...() functions are implicitly linked with the specified database file after `db_attach()` is called.

**Example:**

```
db_attach("/cycles/db/myprogram.db")
```

Attaches the part program to the specified database file.

**See Also:** `dba_query`, `dba_put_master_entry`, `ep_init`

### `dba_get_boolean_parm`

Retrieves a Boolean parameter from the parameter database.

**Syntax:**

```
dba_get_boolean_parm(boolean &ret_value, string query_name, string query_class)
```

**Description:**

Retrieve a Boolean parameter from the parameter database. In the database the value of the entry may be any of: 1|0, true|false, or on|off.

**Parameters:**

| Parameter   | Type    | Description                              |
| ----------- | ------- | ---------------------------------------- |
| ret_value   | boolean | The Boolean value returned from the database (passed by reference) |
| query_name  | string  | The query name used to retrieve the parameter |
| query_class | string  | The query class used to retrieve the parameter |

**Example:**

```
x_rotary = true
dba_get_boolean_parm(&x_rotary, "x.rot_axis", "Dim.Rot_axis")
```

Retrieves whether the `X` axis is rotary or linear.

**See Also:** `dba_get_int_parm`, `dba_get_float_parm`, `dba_get_string_parm`, `dba_put_boolean_parm`

### `dba_get_float_parm`

Retrieves a real number from the parameter database.

**Syntax:**

```
dba_get_float_parm(float &ret_value, string query_name, string query_class)
```

**Description:**

Retrieve a real number from the parameter database.

**Parameters:**

| Parameter   | Type   | Description                              |
| ----------- | ------ | ---------------------------------------- |
| ret_value   | float  | The real number returned from the database (passed by reference) |
| query_name  | string | The query name used to retrieve the parameter |
| query_class | string | The query class used to retrieve the parameter |

**Example:**

```
dry_vel = 0.0
dba_get_float_parm(&dry_vel, "dry_run_velocity", "Cnc")
```

Extracts the parameter for the dry run velocity.

**See Also:** `dba_get_int_parm`, `dba_get_boolean_parm`, `dba_get_string_parm`, `dba_put_float_parm`

### `dba_get_int_parm`

Retrieves an integer from the parameter database.

**Syntax:**

```
dba_get_int_parm(integer &ret_value, string query_name, string query_class)
```

**Description:**

Retrieve an integer from the parameter database. In the database the value may be in the range -2147483648 to +2147483647 and may be in decimal (e.g. 123, -76), hexadecimal (e.g. 0x1B67), or octal (e.g. 017) notation.

**Parameters:**

| Parameter   | Type    | Description                              |
| ----------- | ------- | ---------------------------------------- |
| ret_value   | integer | The integer returned from the database (passed by reference) |
| query_name  | string  | The query name used to retrieve the parameter |
| query_class | string  | The query class used to retrieve the parameter |

**Example:**

```
dba_get_int_parm(&num_buffers, "num_ppb", "Num_ppb")
```

Extracts the parameter for the number of part program buffers.

**See Also:** `dba_get_float_parm`, `dba_get_boolean_parm`, `dba_get_string_parm`, `dba_put_int_parm`

### `dba_get_string_parm`

Retrieves a string parameter from the parameter database.

**Syntax:**

```
dba_get_string_parm(string &ret_str, string query_name, string query_class)
```

**Description:**

Retrieve a string from the parameter database.

**Parameters:**

| Parameter   | Type   | Description                              |
| ----------- | ------ | ---------------------------------------- |
| ret_str     | string | The string returned from the database (passed by reference) |
| query_name  | string | The query name used to retrieve the parameter |
| query_class | string | The query class used to retrieve the parameter |

**Example:**

```
dba_get_string_parm(&image_dir, "dirs.images", "Dirs.Dir")
```

Extracts the parameter for the directory path for images.

**See Also:** `dba_get_int_parm`, `dba_get_float_parm`, `dba_get_boolean_parm`, `dba_put_string_parm`

### `dba_last_parm`

Queries which file the last parameter was found in.

**Syntax:**

```
integer dba_last_parm()
```

**Description:**

This function is used to determine which of the four parameters' database files the last parameter was found in. It is usually called after a dba_get_...() function.

**Returns:**

| Type    | Description                                              |
| ------- | -------------------------------------------------------- |
| integer | One of: `dba_user`, `dba_oem`, `dba_mspec`, or `dba_gen` |

**Example:**

```
dba_get_string_parm(&image_dir, "dirs.images", "Dirs.Dir")
parm_db = dba_last_parm()
if (parm_db = dba_user) then
    write("Parameter found in USER database")
ifend
```

Retrieves the images directory parameter, then calls `dba_last_parm`() to determine which database file it came from, writing a message when it was found in the USER database.

**See Also:** `dba_get_boolean_parm`, `dba_get_int_parm`, `dba_get_float_parm`, `dba_get_string_parm`, `dba_user`, `dba_oem`, `dba_mspec`, `dba_gen`

### `dba_purge_db`

Removes a database file from the DBA's memory cache.

**Syntax:**

```
dba_purge_db(string db_file_name)
```

**Description:**

Remove a database file from the DBA's memory cache. When the Database Administrator requires a database entry it first loads the host database file into its internal memory cache. If a database file is changed externally, the changes are not reflected in database queries if it is already in memory. When the Database Administrator needs to reclaim memory used for a database, it automatically writes the portion of the memory cache to disk, thus overwriting the file. `dba_purge_db()` instructs the Database Administrator to remove the specified database from its internal memory cache so that the next query will load the new version from disk. This function is normally used by applications which create their own database files and install a reference to the file using `dba_put_master_entry()`.

**Parameters:**

| Parameter    | Type   | Description                                       |
| ------------ | ------ | ------------------------------------------------- |
| db_file_name | string | The name of the file to be removed from the cache |

**Additional information:**

1. `dba_purge_db()` does not alter the master database in any way so `dba_put_master_entry()` calls do not need to be repeated.

**Example:**

```
open(&fp, "/db/test.db", append)
write(fp, "\n*abc.def : hello")
close(fp)
dba_purge_db("/db/test.db")
```

Appends a new entry directly to the database file /db/test.db, then purges that file from the DBA's cache so that the next query reloads the updated version from disk.

**See Also:** `dba_put_master_entry`, `dba_put_db_entry`

### `dba_put_boolean_parm`

Writes a Boolean parameter to the parameter database.

**Syntax:**

```
dba_put_boolean_parm(integer location, string storage_key, boolean value)
```

**Description:**

Write a Boolean parameter to the parameter database. This function may only write parameters to the OEM and USER database files. The value written is always stored in the database as "on" or "off".

**Parameters:**

| Parameter   | Type    | Description                              |
| ----------- | ------- | ---------------------------------------- |
| location    | integer | `dba_oem`, `dba_user` specifying which database file |
| storage_key | string  | The storage key for the entry (left hand side of ":"). A "*" is prepended to the storage key before it is written to the database |
| value       | boolean | The value of the entry                   |

**Additional information:**

1. If the target database file (p_oem.db or p_user.db) is read only then this function will not work successfully.

**Example:**

```
dba_put_boolean_parm(dba_user, "lhs", false)
```

The file p_user.db now contains: `*lhs : off`

**See Also:** `dba_get_boolean_parm`, `dba_put_int_parm`, `dba_put_float_parm`, `dba_put_string_parm`, `dba_oem`, `dba_user`

### `dba_put_db_entry`

Inserts an entry into a specific database file.

**Syntax:**

```
dba_put_db_entry(string database, string storage_key, string db_string)
```

**Description:**

Insert a storage key and its associated string into a specific database file. The database file is loaded into the Database Administrator's internal memory cache if not already loaded. The storage key and its associated string are inserted into the database, and the new database is written back to disk.

**Parameters:**

| Parameter   | Type   | Description                                           |
| ----------- | ------ | ----------------------------------------------------- |
| database    | string | The name of the database file                         |
| storage_key | string | The storage key for the entry (left hand side of ":" ) |
| db_string   | string | The string for the entry (right hand side of ":" )     |

**Additional information:**

1. The target file must exist before any entries may be put in it.

**Example:**

```
dba_put_db_entry("/db/test.db", "abc.def", "hello")
```

Inserts the entry `*abc.def : hello` into the database file /db/test.db.

**See Also:** `dba_put_master_entry`, `dba_purge_db`, `dba_query`

### `dba_put_float_parm`

Writes a floating point number parameter to the parameter database.

**Syntax:**

```
dba_put_float_parm(integer location, string storage_key, float value)
```

**Description:**

Writes a real number parameter to the parameter database. This function may only write parameters to the OEM and USER database files. The format of the value written is [-]mmm.ddd, with the number of d's always accommodating the precision of the value. If the exponent is less than -4 then a format [-]m.ddde-xx is used.

**Parameters:**

| Parameter   | Type    | Description                                                                                                                                                                                                                                                                                                       |
| ----------- | ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| location    | integer | This may be `dba_oem` or `dba_user`, specifying which database file to put the entry in.                                                                                                                                                                                                                              |
| storage_key | string  | This string forms the storage key for the entry, i.e. the left hand side of the ":". A "*" is automatically prepended to the storage key before it is written to the database. The "*" is required for language and variant independent entries; for language and variant dependent entries the "*" is redundant. |
| value       | float   | The value of the entry, i.e. the number written to the right hand side of the ":".                                                                                                                                                                                                                                |

**Additional information:**

1. If the target database file (p_oem.db or p_user.db) is read only then this function will not work successfully.

**Example:**

```
dba_put_float_parm(dba_user, "lhs", 123.45678)
```

Writes the floating point value 123.45678 under the storage key `*lhs` into the USER parameter database (p_user.db).

**See Also:** `dba_get_float_parm`, `dba_put_int_parm`, `dba_put_boolean_parm`, `dba_put_string_parm`, `dba_oem`, `dba_user`

### `dba_put_int_parm`

Writes an integer parameter to the parameter database.

**Syntax:**

```
dba_put_int_parm(integer location, string storage_key, integer value)
```

**Description:**

Write an integer parameter to the parameter database. This function may only write parameters to the OEM and USER database files.

**Parameters:**

| Parameter   | Type    | Description                              |
| ----------- | ------- | ---------------------------------------- |
| location    | integer | `dba_oem`, `dba_user` specifying which database file |
| storage_key | string  | The storage key for the entry (left hand side of ":") |
| value       | integer | The value of the entry                   |

**Additional information:**

1. If the target database file (p_oem.db or p_user.db) is read only then this function will not work successfully.

**Example:**

```
dba_put_int_parm(dba_user, "lhs", 1234)
```

The file p_user.db now contains: `*lhs : 1234`

**See Also:** `dba_get_int_parm`, `dba_put_float_parm`, `dba_put_boolean_parm`, `dba_put_string_parm`, `dba_oem`, `dba_user`

### `dba_put_master_entry`

Inserts an entry into the Master Database.

**Syntax:**

```
dba_put_master_entry(string storage_key, string value)
```

**Description:**

Insert an entry into the Master Database. The entry is the path name of a database file. If the path name is relative, then it is relative to "/sys32s/target/<Prd_code>/db" where <Prd_code> is the product code of the machine.

**Parameters:**

| Parameter   | Type   | Description                              |
| ----------- | ------ | ---------------------------------------- |
| storage_key | string | The storage key for the database entry (left hand side of ":") |
| value       | string | The path to the database file (right hand side of ":") |

**Example:**

```
dba_put_master_entry("*config*mypr2", "/cycles/db/config/mypr2.db")
dba_put_master_entry("*menu*mypr2", "/cycles/db/menu/mypr2.db")
```

Installs master database entries for configuration and menu database files.

**See Also:** `dba_put_db_entry`, `dba_purge_db`, `db_attach`

### `dba_put_string_parm`

Writes a string parameter to the parameter database.

**Syntax:**

```
void dba_put_string_parm(integer location, string storage_key, string value)
```

**Description:**

Write a string parameter to the parameter database. May only write parameters to the OEM and USER database files.

**Parameters:**

| Parameter   | Type    | Description                                                                 |
| ----------- | ------- | --------------------------------------------------------------------------- |
| location    | integer | `dba_oem`, `dba_user` specifying which database file to write to          |
| storage_key | string  | Forms the storage key (left hand side of `:`, a `*` is automatically prepended) |
| value       | string  | The value of the entry (right hand side of `:`)                             |

**Additional information:**

1. If the target database file (p_oem.db or p_user.db) is **read only**, this function will not work successfully.
2. If an error condition is encountered, an execution error will be displayed.

**Example:**

```
dba_put_string_parm(dba_user, "lhs", "rhs")
```

Installs entry `*lhs : rhs` into p_user.db.

**See Also:** `dba_put_int_parm`, `dba_put_float_parm`, `dba_put_boolean_parm`, `dba_query`

### `dba_query`

Queries the database for a string value.

**Syntax:**

```
string dba_query(string appl_name, string query_name, string query_class)
```

**Description:**

Query the database for a string. Extracts a string from the database using the application's name, retrieval key, and native language to find the best match entry. Returns the string on the right hand side of the `:` with leading and trailing whitespace stripped.

**Parameters:**

| Parameter   | Type   | Description                                                                 |
| ----------- | ------ | --------------------------------------------------------------------------- |
| appl_name   | string | The application name (added to query_name, class "Appl" is added to query_class) |
| query_name  | string | Retrieval name for "best match" entry                                      |
| query_class | string | Retrieval class for "best match" entry                                     |

**Returns:**

| Type   | Description                               |
| ------ | ----------------------------------------- |
| string | The string value from the database entry  |

**Additional information:**

1. This is the recommended function for retrieving data from database files (except for parameters' database files).
2. Automatic type casting makes it easy to extract different data types.
3. If no match is found, an execution error will be raised.

**Example:**

```
{ Database entry: *value1 : 123.456 }
fv1 = dba_query("test_appl", "value1", "Parameter")
```

The variable `fv1` gets value 123.456 (automatic type casting).

**See Also:** `dba_get_string_parm`, `dba_get_int_parm`, `dba_get_float_parm`, `db_attach`

### `dba_query_lang`

Returns the machine's current native language code.

**Syntax:**

```
string dba_query_lang()
```

**Description:**

Queries the Database Administrator for the machine's current native language and returns it as a short language code string (for example "eng" or "jap"). The returned code is typically used to select language-specific behaviour or messages.

**Returns:**

| Type   | Description                                                              |
| ------ | ------------------------------------------------------------------------ |
| string | The machine's current native language code (for example "eng" or "jap"). |

**Example:**

```
current_lang = dba_query_lang()
```

Retrieves the machine's current native language code into current_lang (for example "eng").

**See Also:** `dba_query`

### `dba_variant_contains`

Scans the machine's variant for a matching component.

**Syntax:**

```
integer dba_variant_contains(string variant_component)
```

**Description:**

Scans the machine's variant for a matching component. It is used to determine if the machine is an element of a particular machine type set.

**Parameters:**

| Parameter         | Type   | Description                          |
| ----------------- | ------ | ------------------------------------ |
| variant_component | string | The variant component to be matched. |

**Returns:**

| Type    | Description                                                                                             |
| ------- | ------------------------------------------------------------------------------------------------------- |
| integer | 0 if no match was found. Non-zero values indicate the level at which the variant component was matched. |

**Example:**

```
match_level = dba_variant_contains("laser")
```

Scans the machine's variant for the component laser; match_level is 0 if it is not present, otherwise the level at which the component matched.

**See Also:** `dba_query_lang`, `dba_query`

### `define`

Assigns a part-program label to a global variable so it can be referenced by name.

**Syntax:**

```
define label variable
```

**Description:**

The `define` command allows a local variable name to reference a global variable not created by PLC and independent of PLC. For example a global variable such as g_bv1 can be assigned a variable name, which is then referenced within the program with a % prefix (for example %START_FLAG). This allows the entire program to be written using local variable names which are linked to a global value in one position only.

**Parameters:**

| Parameter | Type | Description                                                                                                  |
| --------- | ---- | ------------------------------------------------------------------------------------------------------------ |
| label     | -    | The local name being defined; referenced elsewhere in the program with a % prefix (for example %START_FLAG). |
| variable  | -    | The global variable that the label refers to (for example g_bv1).                                            |

**Additional information:**

1. DEFINEd variables are local to the current part program only.
2. The `define` set of expressions must be repeated in any other program using the same labels.
3. DEFINEd variables must be declared before any subroutine using these labels.
4. DEFINEd variables cannot be accessed by subprogram call unless it also declares the same labels.
5. When `define` is used in an executable .def program executed at startup, DEFINEd variables become global for all part programs.

**Example:**

```
define START_FLAG g_bv1
```

Defines the label START_FLAG for the global variable g_bv1; the program then refers to it as %START_FLAG.

**See Also:** No related items

### `detach`

Detaches a Part Program Processor from its current Logical Machine or detaches an axis.

**Syntax:**

```
detach axis
detach axis(axis_id)
detach lm
```

**Description:**

The `detach` axis command allows an axis to be detached from the current logical machine so that another Part Program Processor may attach it with `attach` axis. `detach` Logical Machine detaches a Part Program Processor from its current Logical Machine. 


**Parameters:**

| Parameter | Type    | Description                           |
| --------- | ------- | ------------------------------------- |
| axis      | letter  | Axis to be detached (e.g., `A`, `B`, `C`)   |
| axis_id   | integer | Axis index to be detached. Use this with the `axis` function               |
| lm   | - | use `lm` to detach part program processor from the current logical machine               |

**Additional information:**

1. Soft axis cannot be detached.
2. Axes assigned to ordinates 1-3 cannot be detached.
3. An axis cannot be detached if it's the only axis on a logical machine.
4. An axis cannot be detached if its ordinate number is also used on another logical machine. For example, if `A` axis is assigned to ordinate 4 on logical machine 1 and `C` axis is assigned to ordinate 4 on logical machine 2, then neither of these axes can be detached.
5. This command can only detach an axis from the current logical machine i.e. the logical machine that the Part Program Processor is currently attached to.
6. When the `attach` LM command is used to attach a Part Program Processor to a logical machine, any axes that had previously been detached from that logical machine will be reattached.


**Example 1:**

```
detach axis(3)
```

Detaches axis number 3 from the current logical machine attached to the part program processor.

**Example 2:**

```
detach lm
```

Causes the currently-attached logical machine to be detached from the Part Program Processor.

**See Also:** `attach`

### `device_get_maximum`

Retrieves the maximum possible value of a parameter on a digital device.

**Syntax:**

```
integer device_get_maximum(integer device, integer object_index, integer entry_subindex)
```

**Description:**

Retrieves the maximum possible value of object index / entry subindex parameter on a digital device.

**Parameters:**

| Parameter      | Type    | Description                              |
| -------------- | ------- | ---------------------------------------- |
| device         | integer | The logical device number.               |
| object_index   | integer | The object index parameter to be read.   |
| entry_subindex | integer | The entry subindex parameter to be read. |

**Returns:**

| Type    | Description                                                                                                                                                                         |
| ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| integer | The maximum possible value for the specified parameter. Note that a return value of 0.0 may indicate that no maximum value is applicable or that the parameter is not configurable. |

**Example:**

```
device = 1
object_index = 24770
entry_subindex = 1
maximum = device_get_maximum(device, object_index, entry_subindex)
```

Reads the maximum possible value of the parameter at object index 24770, entry subindex 1 on device 1 into `maximum`.

**See Also:** `device_get_minimum`

### `device_get_minimum`

Retrieves the minimum possible value of a parameter on a digital device.

**Syntax:**

```
integer device_get_minimum(integer device, integer object_index, integer entry_subindex)
```

**Description:**

Retrieves the minimum possible value of object index / entry subindex parameter on a digital device.

**Parameters:**

| Parameter      | Type    | Description                              |
| -------------- | ------- | ---------------------------------------- |
| device         | integer | The logical device number.               |
| object_index   | integer | The object index parameter to be read.   |
| entry_subindex | integer | The entry subindex parameter to be read. |

**Returns:**

| Type    | Description                                                                                                                                                                   |
| ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| integer | The minimum possible value for the specified parameter. A return value of 0.0 may indicate that there is no minimum value applicable or that the parameter is not adjustable. |

**Example:**

```
device = 1
object_index = 24770
entry_subindex = 1
minimum = device_get_minimum(device, object_index, entry_subindex)
```

Reads the minimum possible value of the parameter at object index 24770, entry subindex 1 on device 1 into `minimum`.

**See Also:** `device_get_maximum`, `device_get_value`, `device_get_name`

### `device_get_name`

Retrieves the name of a parameter on a digital device.

**Syntax:**

```
string device_get_name(integer device, integer object_index, integer entry_subindex)
```

**Description:**

Retrieves the name component of object index / entry subindex parameter on a digital device.

**Parameters:**

| Parameter      | Type    | Description                              |
| -------------- | ------- | ---------------------------------------- |
| device         | integer | The logical device number.               |
| object_index   | integer | The object index parameter to be read.   |
| entry_subindex | integer | The entry subindex parameter to be read. |

**Returns:**

| Type   | Description                                                                                             |
| ------ | ------------------------------------------------------------------------------------------------------- |
| string | The name of the specified parameter. If the name is not found, the function may return an empty string. |

**Example:**

```
device = 1
object_index = 24770
entry_subindex = 1
name = device_get_name(device, object_index, entry_subindex)
```

Reads the name of the parameter at object index 24770, entry subindex 1 on device 1 into `name`.

**See Also:** `device_get_value`, `device_get_maximum`, `device_get_minimum`

### `device_get_value`

Retrieves the value of a parameter from a digital device.

**Syntax:**

```
float device_get_value(integer device, integer object_index, integer entry_subindex)
```

**Description:**

This function retrieves a value of object index / entry subindex parameter from a specific device.

**Parameters:**

| Parameter      | Type    | Description                              |
| -------------- | ------- | ---------------------------------------- |
| device         | integer | The logical device number.               |
| object_index   | integer | The object index parameter to be read.   |
| entry_subindex | integer | The entry subindex parameter to be read. |

**Returns:**

| Type  | Description                           |
| ----- | ------------------------------------- |
| float | The value of the specified parameter. |

**Example:**

```
device = 1
object_index = 24770
entry_subindex = 1
value = device_get_value(device, object_index, entry_subindex)
```

Reads the value of the parameter at object index 24770, entry subindex 1 on device 1 into `value`.

**See Also:** `device_set_value`, `device_get_maximum`, `device_get_minimum`

### `device_run_homing`

Initiates drive-controlled homing for the specified logical device.

**Syntax:**

```
integer device_run_homing(integer logical_device_number)
```

**Description:**

Initiates the drive-controlled homing for the specified logical device.

Since not all drives support the same functionality and/or interface, the following is a non-exhaustive list of common configuration parameters for drive-controlled homing:

- Homing type (i.e. index pulse search in positive direction, index pulse search in negative direction, home switch search followed by index pulse search, home to current position, etc)
- Home offset
- Homing velocity
- Homing acceleration

Ensure that you review the manual for your selected drives to determine the homing configuration data they require.

**Parameters:**

| Parameter             | Type    | Description                                                             |
| --------------------- | ------- | ----------------------------------------------------------------------- |
| logical_device_number | integer | The logical device that will be performing the drive-controlled homing. |

**Returns:**

| Type    | Description                                                                                                                                      |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| integer | A return code indicating the homing result: 0 = Success, 1 = Failed, 2 = Homing Not Supported, 3 = Aborted, 4 = System Error, 5 = Unknown Error. |

**Additional information:**

1. The servo drive configuration for the homing procedure must be set before this function is called.
2. A single call to this function can include one or more drive-controlled moves (depends on the homing type that has been configured to the drive).
3. During this function, EPPL execution on the current PPP will pause until the homing is complete (either success or failure).
4. The home offset will be automatically applied by the servo drive at the appropriate point in the homing sequence.
5. After this function ends, the CNC will re-prime the axis position with the servo drive actual position (on both success and failure).
6. When this function starts, the drive will be moved into the homing operating mode.
7. When this function ends, the drive will be moved into the position operating mode (on both success and failure).
8. During this function E-Stop and Abort will be available.
9. During this function Feedhold, Feedrate Override and Machine Wait (via ILB_WAIT) are not available.

**Example:**

```
result = device_run_homing(1)
```

Initiates drive-controlled homing on logical device 1 and stores the return code in `result`.

**See Also:** `reprimecp`

### `device_set_value`

Sets the value of a parameter on a specific device.

**Syntax:**

```
device_set_value(integer device, integer object_index, integer entry_subindex, float value)
```

**Description:**

This function sets the value of an object index / entry subindex parameter to a specific device.

**Parameters:**

| Parameter      | Type    | Description                                      |
| -------------- | ------- | ------------------------------------------------ |
| device         | integer | The logical device number.                       |
| object_index   | integer | The object index parameter to be set.            |
| entry_subindex | integer | The entry subindex parameter to be set.          |
| value          | float   | The actual value passed to the device to be set. |

**Example:**

```
device = 1
object_index = 24770
entry_subindex = 1
value = 1.0
device_set_value(device, object_index, entry_subindex, value)
```

Sets the parameter at object index 24770, entry subindex 1 on device 1 to the value 1.0.

**See Also:** `device_get_value`, `device_get_maximum`, `device_get_minimum`

### `dimension words`

Dimension words cause machine motion according to the current modal conditions, or act as parameters for certain preparatory words and canned cycles.

**Syntax:**

```
{ Non-configurable }
X Y Z U V W P Q R A B C X' Y' Z' U' V' A' B' C' W' P' Q' R'

{ Default set by p_gen.db }
A1 B1 C1 P1 Q1 R1 U1 V1 W1 X1 Y1 Z1 A2 B2 C2 P2 Q2 R2 U2 V2 W2 X2 Y2 Z2
```

**Description:**

A dimension word consists of a dimension variable (one of the addresses shown in Syntax) followed by either an expression in brackets or a number value. A maximum of one dimension word of each letter address can be programmed in each block.

The `p_gen.db` database defines the default value for the axis label, while the joint index is directly linked to the axis index. A user can reassign the axis label using the parameter database, provided the new label begins with a supported single-letter axis name (upper or lower case), is followed by an unsigned integer between 1 and 9, and does not duplicate an existing axis label. This allows the labelling of the axes to be customised to preference.

Dimension words are also accessible as variables, where the variable takes on its last programmed value. The dimension word variables may, however, also be modified by other preparatory modes, so a dimension word will not always reflect the machine position. The programmed `sync` command causes the last programmed machine position (in user frame coordinates) to be latched back into the dimension word variables.

Dimension words that are left out of a block will generally take their previous values.

**Additional information:**

1. Modality in part programs: dimension words relating to mode 0 or mode 1 preparatory words take on values dependent on the preparatory word if they are not programmed in a block, whereas dimension words relating to mode 2 preparatory words take on their previous values if they are not programmed in a block. For example, after `G1 X10 Y20` (`G1` is a mode 2 preparatory word), a following block `X30` leaves `Y` at 20 because it is not programmed.
2. Because other preparatory modes may modify the dimension word variables, they do not always reflect position. For example, `N1 G1 X(20)`, `N2 dwell X(0.03)`, `N3 G1 X(x * 2)` results in block `N3` moving to X = 0.06, not X = 40, because the `dwell` block overwrote the `X` variable.
3. The `AXIS(axis_id)` keyword allows an axis to be commanded by its axis number, as an alternative to commanding it via its dimension word

**Example:**

```
U(25.4)
X(fv6)
B(-4.72)
Z((fv3 * 3.66) + fv17)

G1 X20
G50 X(X + 20)   { X in the bracket is 20, its last programmed value; equals G50 X(40) }

linear X10 Y20 Z30
X20             { will move to x20 y20 z30 }
Z0              { will move to x20 y20 z0 }
```

The first group shows dimension words programmed with a number value and with bracketed expressions. In the second group, a dimension word used inside an expression takes on its last programmed value. In the third group, dimension words omitted from a block retain their previous values.

**See Also:** `axis`, `sync`

### `dtor`

Converts degrees to radians.

**Syntax:**

```
float dtor(float expr)
```

**Description:**

Convert degrees to radians. The expression expr is assumed to be in units of degrees.

**Parameters:**

| Parameter | Type  | Description                                 |
| --------- | ----- | ------------------------------------------- |
| expr      | float | The angle, in units of degrees, to convert. |

**Returns:**

| Type  | Description                     |
| ----- | ------------------------------- |
| float | The angle expressed in radians. |

**Example:**

```
dtor(30.0)
```

Returns 0.5236.

**See Also:** `rtod`

### `eff`

Sets effector offsets for machines with pivoting tools.

**Syntax:**

```
eff
eff I value J value K value
eff D group_number
```

**Description:**

Effector offsets are used to compensate for the dimensions of a tool in machines with pivoting tools. Unlike tool offsets, effector offsets allow the tool to be rotated while maintaining the correct position of the reference point on the tool. Effector offsets are programmed explicitly by eff followed by interpolation words which specify the offset vector; any interpolation words not programmed remain at their previously programmed value. If eff is programmed without any interpolation words, all effector offsets are set to zero. Effector offsets may also be programmed indirectly by eff followed by `D`, `H` or `tooloffset` and a tool table offset group number (0-41) from which the interpolation word data is taken.

**Parameters:**

| Parameter    | Type    | Description                                                                                                                |
| ------------ | ------- | -------------------------------------------------------------------------------------------------------------------------- |
| I, J, K      | float   | Effector offset vector components (interpolation words).                                                                   |
| group_number | integer | Tool table offset group (0-41) whose entry supplies the offset, when programmed indirectly with `D`, `H` or `tooloffset`.        |

**Additional information:**

1. `eff` without interpolation words sets all effector offsets to zero.

**Example:**

```
eff D6
eff I-50 K-30.37
```

The first line sets the effector offset from the vector held in tool offset group 6; the second sets an explicit I/K offset vector.

**See Also:** `effadjust`, `D`, `H`, `tooloffset`

### `effadjust`

Applies a compensation to all effector offsets.

**Syntax:**

```
effadjust I(i_adj) J(j_adj) K(k_adj)
```

**Description:**

The effector offset adjustment command allows a compensation to be applied to all effector offsets. When used prior to a normal eff command, `eff I(i_o) J(j_o) K(k_o)`, the result of the two commands is the same as issuing `eff I(i_o+i_adj) J(j_o+j_adj) K(k_o+k_adj)`. The adjustment applies to all effector offsets, including those applied by `D` or `tooloffset` arguments and the zero offset of a bare eff command.

**Parameters:**

| Parameter           | Type  | Description                                                             |
| ------------------- | ----- | ----------------------------------------------------------------------- |
| i_adj, j_adj, k_adj | float | Adjustment values applied to the I, J and K effector offset directions. |

**Additional information:**

1. `effadjust` contains an internal sync, so it should not be used unless necessary (it cancels lookahead, causes motion to halt, and takes significant processing).
2. The SMA variables `g_eff_adjust`<0,1,2> reflect the current value of the adjustment.
3. The adjustment is set to zero on start-up and remains until altered or shutdown; if it must persist over a shutdown it should be written to the Parameters database and reloaded via an `effadjust` call at machine-on.

**Example:**

```
effadjust I(i_adj) J(j_adj) K(k_adj)
```

Applies the adjustment vector (i_adj, j_adj, k_adj) to all effector offsets, so a subsequent bare eff or an eff with `D`/`tooloffset` offsets is shifted by that vector.

**See Also:** `eff`, `D`, `tooloffset`, `sync`

### `electronic_cam_disable`

Removes the electronic cam link between a reference and follower axis.

**Syntax:**

```
electronic_cam_disable(reference, follower)
electronic_cam_disable()
```

**Description:**

Disables the link between the reference axis and the follower axis. The follower axis can be commanded with standard move blocks after calling this function. When called with no arguments, it disables the links between all reference axes and follower axes, equivalent to calling `electronic_cam_disable` for each currently active reference and follower axis pair.

**Parameters:**

| Parameter | Type   | Description                                                                   |
| --------- | ------ | ----------------------------------------------------------------------------- |
| reference | string | Reference axis, e.g. "X". |
| follower  | string | Follower axis, e.g. "Y".  |

**Example:**

```
electronic_cam_disable("a", "z")
electronic_cam_disable()
```

The first call removes the electronic cam link so the `Z` axis no longer follows the `A` axis; the second removes the links for all reference/follower pairs at once.

**See Also:** `electronic_cam_enable`, `electronic_cam_read_follower_position`

### `electronic_cam_enable`

Links a follower axis to a reference axis (electronic cam).

**Syntax:**

```
electronic_cam_enable(reference, follower, mode, profile_device, period, reference_offset, follower_offset, reference_scaling, follower_scaling)
electronic_cam_enable(reference, follower)
```

**Description:**

Links the movement of the follower axis to the position of the reference axis. Once active, standard move blocks cannot be used to control the follower axis. Mapping multiple follower axes to a single reference axis can be achieved through multiple calls to this function. The first syntax form links the axes through the relationship defined in a lookup table (profile_device). The second syntax form links the axes in a linear 1-to-1 relationship, maintaining whatever offset existed between the two axes before the function was activated.

**Parameters:**

| Parameter         | Type           | Description                                                                                                                                                                                                                                                                                  |
| ----------------- | -------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| reference         | string         | The reference axis used to generate the commands for the follower axis, e.g. "X".                                                                                                                                                                                                            |
| follower          | string         | The axis controlled by the electronic cam system, e.g. "Y".                                                                                                                                                                                                                                  |
| mode              | boolean        | Whether the follower positions in the lookup table are treated as relative (true) or absolute (false). In relative mode the follower commands are offsets relative to the initial position of the axis; the reference positions are always absolute.                                         |
| profile_device    | profile_device | Profile device storing the lookup table mapping reference axis position (column 0) to follower axis command (column 1). Reference positions must be in numerically ascending order; linear interpolation is applied between points.                                                          |
| period            | integer        | Period for the reference axis. If 0 or less the table is non-periodic (the follower holds the first or last position when the reference moves outside the table range); if greater than 0 the table is periodic and may only contain reference positions in the range 0 to period inclusive. |
| reference_offset  | float          | (Optional) Offset applied to the reference axis position before table lookup. Default 0.                                                                                                                                                                                                     |
| follower_offset   | float          | (Optional) Offset applied to the follower axis position after table lookup. Default 0.                                                                                                                                                                                                       |
| reference_scaling | float          | (Optional) Scaling applied to the reference axis position before table lookup. Default 1.                                                                                                                                                                                                    |
| follower_scaling  | float          | (Optional) Scaling applied to the follower axis position after table lookup. Default 1.                                                                                                                                                                                                      |

**Additional information:**

1. The CNC does not apply velocity, acceleration, and jerk limits to the follower axis commands derived from the electronic cam; it is the programmer's responsibility to ensure these commands are within machine limits.
2. A reference axis can have multiple follower axes, but each follower axis may follow only one reference axis.

**Example:**

```
electronic_cam_enable("A", "Z", false, g_iv115, 60)  { Lookup table }
electronic_cam_enable("X", "Y")                       { 1-to-1 }
```

The first call links the `Z` axis to the `A` axis using the lookup table in g_iv115 with a periodic reference period of 60; the second links the `Y` axis to the `X` axis in a linear 1-to-1 relationship.

**See Also:** `electronic_cam_disable`, `electronic_cam_read_follower_position`, `tg_prof_alloc`, `tg_prof_write`

### `electronic_cam_read_follower_position`

Determines the correct follower axis position for enabling electronic cam in absolute mode.

**Syntax:**

```
float electronic_cam_read_follower_position(integer profile_device_id, float period, float reference_axis_position)
```

**Description:**

The `electronic_cam_read_follower_position` function is used in conjunction with the `electronic_cam_enable` function when using absolute mode. In this mode, the follower axis must be moved to the correct position before the electronic cam can be enabled. The `electronic_cam_read_follower_position` function helps determine the correct position that the follower axis needs to be in for the electronic cam to be enabled in absolute mode. If the follower axis is not in the correct position, the electronic cam cannot be enabled and an error message will be raised.

**Parameters:**

| Parameter               | Type    | Description                                          |
| ----------------------- | ------- | ---------------------------------------------------- |
| profile_device_id       | integer | Profile device id that stores a relationship between reference axis and follower axis |
| period                  | float   | Period                                               |
| reference_axis_position | float   | Reference axis position                              |

**Returns:**

| Type  | Description                                                          |
| ----- | -------------------------------------------------------------------- |
| float | A calculated follower axis position from a given reference axis position |

**Example:**

```
follower_start = electronic_cam_read_follower_position(g_iv115, 60, 0)
G1 Z(follower_start)
electronic_cam_enable("A", "Z", false, g_iv115, 60)
```

Using the periodic lookup table held in profile device `g_iv115` (period 60), this reads the follower position that corresponds to reference axis position 0 into `follower_start`. The `Z` (follower) axis is then moved to that position with a normal move block, so that when the electronic cam is enabled in absolute mode the follower is already at the position the table maps to the current reference position, allowing the cam to engage without raising an invalid axis position error.

**See Also:** `electronic_cam_enable`, `electronic_cam_disable`

### `ep_init`

Registers an application with the Error Processor.

**Syntax:**

```
void ep_init(string name)
```

**Description:**

Registers an application with the Error Processor. The name registered is used by the Error Processor to extract application-specific Error and Warning database entries.

**Parameters:**

| Parameter | Type   | Description                                                                             |
| --------- | ------ | --------------------------------------------------------------------------------------- |
| name      | string | The application's registration name (max 16 characters). Forms the application_name component of all database query keys resulting from calls to ep_...() functions. |

**Additional information:**

1. An application may call `ep_init()` any number of times to change the registration name.
2. This function is not required if `db_attach()` is used - `db_attach()` will register the name "pp" automatically.
3. If an error condition is encountered, an execution error describing the offending condition will be displayed.

**Example:**

```
ep_init("myapp")
```

Registers the application with the name "myapp".

**See Also:** `ep_warning`, `db_attach`

### `ep_warning`

Produces a warning message.

**Syntax:**

```
void ep_warning(string warning_name, string warning_class, string args_format, ...)
```

**Description:**

Produces a warning message. Used when a program detects a fault condition but can continue. Opens a window on screen to display an appropriate error message. Execution continues without waiting for user acknowledgment.

**Parameters:**

| Parameter     | Type   | Description                                                         |
| ------------- | ------ | ------------------------------------------------------------------- |
| warning_name  | string | Retrieval name for the warning heading and message format from database |
| warning_class | string | Retrieval class for the warning heading and message from database   |
| args_format   | string | String containing conversion specifiers (%b, %B, %D, %f, %s)        |
| ...           | varies | Zero or one argument corresponding to the conversion specifier      |

**Additional information:**

1. `ep_init()` must be called before `ep_warning()` can be used.
2. EPPL can only take at most one argument in the variable argument list.
3. If an error condition is encountered, an execution error will be displayed.

**Example:**

```
ep_warning("warn_name", "Warning", "%f", fv1)
```

Displays a warning message with the value of fv1.

**See Also:** `ep_init`

### `exp`

Returns e raised to the power of an expression.

**Syntax:**

```
float exp(float expr)
```

**Description:**

Exponential base e. Return e raised to the power expr.

**Parameters:**

| Parameter | Type  | Description                        |
| --------- | ----- | ---------------------------------- |
| expr      | float | The exponent to which e is raised. |

**Returns:**

| Type  | Description                 |
| ----- | --------------------------- |
| float | e raised to the power expr. |

**Example:**

```
exp(2.0)
```

Returns 7.3890.

**See Also:** `expten`, `exptwo`, `log`, `logten`, `logtwo`

### `expten`

Returns 10 raised to the power of an expression.

**Syntax:**

```
float expten(float expr)
```

**Description:**

Exponential base 10. Return 10 raised to the power expr.

**Parameters:**

| Parameter | Type  | Description                         |
| --------- | ----- | ----------------------------------- |
| expr      | float | The exponent to which 10 is raised. |

**Returns:**

| Type  | Description                  |
| ----- | ---------------------------- |
| float | 10 raised to the power expr. |

**Example:**

```
expten(2.0)
```

Returns 100.0.

**See Also:** `exp`, `exptwo`, `log`, `logten`, `logtwo`

### `exptwo`

Returns 2 raised to the power of an expression.

**Syntax:**

```
float exptwo(float expr)
```

**Description:**

Exponential base 2. Return 2 raised to the power expr.

**Parameters:**

| Parameter | Type  | Description                        |
| --------- | ----- | ---------------------------------- |
| expr      | float | The exponent to which 2 is raised. |

**Returns:**

| Type  | Description                 |
| ----- | --------------------------- |
| float | 2 raised to the power expr. |

**Example:**

```
exptwo(5.0)
```

Returns 32.0.

**See Also:** `exp`, `expten`, `log`, `logten`, `logtwo`

### `extint_disable`

Disables an external interrupt.

**Syntax:**

```
extint_disable(integer interrupt_number)
```

**Description:**

Disables an external interrupt by applying its mask. The associated `XOLB_WAITINGFOR_EXTINTx` bit is cleared.

**Parameters:**

| Parameter        | Type    | Description                                                    |
| ---------------- | ------- | -------------------------------------------------------------- |
| interrupt_number | integer | The external interrupt number to disable, in the range 1 to 4. |

**Example:**

```
extint_disable(1)
```

Disables external interrupt 1 by masking it and clearing `XOLB_WAITINGFOR_EXTINT1`.

**See Also:** `extint_enable`, `extint_set_default_operation`

### `extint_enable`

Enables an external interrupt.

**Syntax:**

```
extint_enable(integer interrupt_number)
```

**Description:**

Enables an external interrupt by removing its mask. A pending interrupt is cleared before the mask is removed, and the associated `XOLB_WAITINGFOR_EXTINTx` bit is set.

**Parameters:**

| Parameter        | Type    | Description                                                   |
| ---------------- | ------- | ------------------------------------------------------------- |
| interrupt_number | integer | The external interrupt number to enable, in the range 1 to 4. |

**Example:**

```
extint_enable(1)
```

Enables external interrupt 1, clearing any pending interrupt and arming `XOLB_WAITINGFOR_EXTINT1`.

**See Also:** `extint_disable`, `extint_set_default_operation`

### `extint_set_default_operation`

Installs the default interrupt service routine for an external interrupt.

**Syntax:**

```
integer extint_set_default_operation(integer interrupt_number)
```

**Description:**

Sets the default interrupt service routine for an external interrupt. The default operation clears the associated `XOLB_WAITINGFOR_EXTINTx` bit, and after the interrupt occurs, the mask is automatically applied to avoid further interrupts.

**Parameters:**

| Parameter        | Type    | Description                                                                                    |
| ---------------- | ------- | ---------------------------------------------------------------------------------------------- |
| interrupt_number | integer | The external interrupt number whose default service routine is installed, in the range 1 to 4. |

**Returns:**

| Type    | Description                                                                        |
| ------- | ---------------------------------------------------------------------------------- |
| integer | 0 on success, or a non-zero in-use code if the interrupt vector is already in use. |

**Example:**

```
extint_set_default_operation(1)
```

Installs the default interrupt service routine for external interrupt 1, returning 0 when it is installed successfully.

**See Also:** `extint_enable`, `extint_disable`

### `fabs`

Returns the absolute value of a floating point expression.

**Syntax:**

```
float fabs(float expr)
```

**Description:**

Return the absolute value of the expression expr. as a float.

**Parameters:**

| Parameter | Type  | Description                                      |
| --------- | ----- | ------------------------------------------------ |
| expr      | float | The expression whose absolute value is returned. |

**Returns:**

| Type  | Description                             |
| ----- | --------------------------------------- |
| float | The absolute value of expr. |

**Example:**

```
fabs(-10.205)
```

Returns 10.205.

**See Also:** `abs`, `trunc`, `round`

### `fdelete`

Deletes unwanted or temporary files.

**Syntax:**

```
fdelete(filename)
```

**Description:**

EPPL command `fdelete` is used to delete unwanted or temporary files in AMCore releases (unlike `fexists`, `fdelete` is not available within a system command). This command runs in a quiet mode and will not ask the user again before deleting files. This command will not delete a `read`-ONLY file.

**Parameters:**

| Parameter | Type   | Description                                                                                                                                                                                                                 |
| --------- | ------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| filename  | string | An expression which is typecast to a string, representing the name of the file. A relative path name (e.g. "out.data" or "data/out.data") is relative to OEMPATH. Wildcard characters are accepted as part of the filename. |

**Example:**

```
fdelete "/OEM/delete_this*.pp"
sv1 = ("c:\\test1.txt")
fdelete(sv1)
```

Deletes the files matching the wildcard path, then deletes the file whose name is held in the string variable sv1, showing that a variable may be passed to the instruction.

**See Also:** `fexists`, `open`, `close`

### `feedgroup`

Selects which axes are included in the feedrate calculation.

**Syntax:**

```
feedgroup dimension_word1 dimension_word2 ...
```

**Description:**

If `feedgroup` is followed by one or more dimension words, the CNC includes the corresponding axes in feedrate calculation. If `feedgroup` is called without any dimension words, any previous `feedgroup` command is cancelled. This means that all axes in a move are included in feedrate calculation.

**Parameters:**

| Parameter           | Type | Description                                                                                                                                         |
| ------------------- | ---- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| dimension_word1 ... | axis | One or more dimension words naming the axes (e.g. `X`, `Y`) to include in the feedrate calculation. If none are given, any previous `feedgroup` command is cancelled. |

**Additional information:**

1. `feedgroup` only affects linear and spline moves.
2. If none of the axes specified by `feedgroup` participate in a move, that move is performed ignoring the `feedgroup` command. For example, if `feedgroup X` is commanded, `G1 Y100 Z100 A90` runs as if `feedgroup` was never used.

**Example:**

```
feedgroup X
G91 G1 X100 Y200 F100
```

Because only the `X` axis is in the feed group, the `X` axis moves at the feedrate of 100 mm/min while the `Y` axis moves at 200 mm/min, so both axes reach the target at the same time.

**See Also:** `F`, `G1`, `unitcv`

### `fexists`

Checks whether a specified file exists.

**Syntax:**

```
integer fexists(filename)
```

**Description:**

`fexists` checks whether a specified file exists.

**Parameters:**

| Parameter | Type   | Description                                                                                                                |
| --------- | ------ | -------------------------------------------------------------------------------------------------------------------------- |
| filename  | string | An expression which is typecast to a string, representing the name of the file. Environment variable expansion is allowed. |

**Returns:**

| Type    | Description                                                                                                            |
| ------- | ---------------------------------------------------------------------------------------------------------------------- |
| integer | A return code: 0 = file does not exist; 1 = file exists but unable to access; 2 = file exists and able to access file. |

**Example:**

```
iv1 = fexists("c:\\test.txt")
sv1 = ("c:\\test1.txt")
iv1 = fexists(sv1)
```

Tests whether the literal path exists, storing the return code in iv1, then repeats the test using a filename held in the string variable sv1, showing that a variable may be passed to the instruction.

**See Also:** `fdelete`, `open`, `close`

### `fillet`

Adds a tangential corner-rounding arc between two moves.

**Syntax:**

```
fillet radius
```

**Description:**

A fillet is an arc of (usually) relatively small radius which is positioned such that it is tangential to the two moves it connects where it touches each of them. The value assigned to a fillet when it is programmed represents the radius of the fillet. The fillet clips the tail of the move it is defined with and the head of the following move. A fillet is programmed by fillet followed by either an expression in brackets or a number. A fillet may be programmed on linear, rapid or helical interpolation moves.

**Parameters:**

| Parameter | Type  | Description                                                                 |
| --------- | ----- | --------------------------------------------------------------------------- |
| radius    | float | The radius of the fillet arc; either a number or an expression in brackets. |

**Additional information:**

1. 2D CRC may be applied to moves that have a fillet modifier.
2. A fillet is calculated as an exact circular or helical arc and may be used as a functional item in the part geometry.
3. The following move that will be clipped to perform the fillet need not be the next block in the program; it may be separated by up to 100 calculation blocks from the move with the fillet applied.
4. If path lookahead needs to be cancelled before the next interpolation block is found, the fillet will be ignored.
5. If one of the moves to be clipped is too short to be filleted, the fillet will be ignored.
6. A zero radius fillet will be ignored.
7. Fillets will always be traversed at the programmed feedrate (even if the moves being filleted are rapid moves.
8. `fillet` is a block modifier -- it cannot be used as a standalone statement. It must appear on a motion block.

**Example:**

```
relative
N10 arccw Y-48 rad30 fillet 4
N20 linear X53
```

N10 traverses a clockwise arc of radius 30 with a fillet of radius 4 applied at its intersection with the following move; N20 is the linear move that the fillet is clipped into.

**See Also:** `chamfer`, `arccw`, `linear`, `rad`

### `fit_polynomial`

Calculates polynomial coefficients for a best-fit curve of a given data set.

**Syntax:**

```
integer fit_polynomial(integer data_profile_device_id, integer order)
integer fit_polynomial(integer data_profile_device_id, integer order, integer &scale_and_centre_profile_device_id)
```

**Description:**

Calculate the coefficients for a polynomial for the given data set that is a best fit (using least squares regression). The number of data points must be greater than the number of order + 1. This function can create up to 2 profile devices and they should be freed when no longer used.

**Parameters:**

| Parameter                          | Type    | Description                                                                                                                                             |
| ---------------------------------- | ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| data_profile_device_id             | integer | The profile ID of the profile device containing the data points where x data is in column 0 and y data is in column 1.                                  |
| order                              | integer | Order of a polynomial used for curve fitting.                                                                                                           |
| scale_and_centre_profile_device_id | integer | (Optional) The profile ID of the profile device containing the mean (row 0, column 0) and the standard deviation (row 1, column 0) of a given data set. |

**Returns:**

| Type    | Description                                                                                                                                                                                                                                               |
| ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| integer | The profile ID of the profile device containing the coefficients in an ascending power. Each coefficient is stored in column 0 of each row. If an error condition is encountered an execution error describing the offending condition will be displayed. |

**Example:**

```
{ Create profile device to hold data points }
pri_prof = tg_prof_alloc(16, 2)

{ Dataset }
tg_prof_write(pri_prof, 23398.0, 0.20, 0)
tg_prof_write(pri_prof, 23531.0, 0.50, 1)
tg_prof_write(pri_prof, 23574.0, 0.7, 2)
tg_prof_write(pri_prof, 23620.0, 1.00, 3)

coeff_id = fit_polynomial(pri_prof, 8, &scale_and_centre_profile_id)

{ The coefficients in p are in ascending powers }
tg_prof_read(coeff_id, &(CNC)fv0, 0)
tg_prof_read(coeff_id, &(CNC)fv1, 1)
```

Allocates a profile device for the data points, writes the x/y data set into it, fits an 8th-order polynomial, and reads the resulting coefficients (in ascending powers) from the returned profile device, into variables `fv0` and `fv1`.

**See Also:** `tg_prof_alloc`, `tg_prof_write`, `tg_prof_read`, `tg_prof_free`

### `fm`

Selects the feedrate mode when starting a spline block.

**Syntax:**

```
fm mode
fm(expression)
```

**Description:**

When starting a spline block using the `splineon` command, you can select one of two available feedrate modes. 

Step feedrate mode is selected by commanding `SPLINEON FM0`. In step feedrate mode, if you specify a feedrate for a spline segment, the feedrate will change as fast as possible at the beginning of that spline segment (while adhering to jerk and acceleration limits). 

Continuous feedrate mode is selected by commanding `SPLINEON FM1`. In continuous feedrate mode, if you specify a different feedrate for every spline segment, the feedrate will change continuously. This means that the feedrate will be changing along the spline segment rather than changing only at the beginning of the segment. 

If you do not specify any feedrate modes, the default feedrate mode specified by the `spl_feedrate_mode` database parameter will be used. If this parameter is set to `0`, step feedrate mode is used as the default. If it is set to `1`, continuous feedrate mode will be the default feedrate mode.

**Parameters:**

| Parameter  | Type       | Description                                                                                             |
| ---------- | ---------- | ------------------------------------------------------------------------------------------------------- |
| mode       | integer    | `0` for step feedrate mode, `1` for continuous feedrate mode.                                            |
| expression | expression | An expression evaluating to `0` or `1`.                                                                  |

**Example:**

```
F200 splineon fm0
F200 splineon fm1
```

Starts a spline block at feedrate 200 in step feedrate mode (`fm0`), and alternatively in continuous feedrate mode (`fm1`).

**See Also:** `splineon`, `splineoff`, `F`, `feedrate`, `vpv`, `vpl`

### `gbif`

Calls a General Purpose Built-In Function developed by application programmers.

**Syntax:**

```
gbif("name", arg1, arg2 ...)
```

**Description:**

General Purpose Built-In Functions (`gbif`) can be developed by application programmers. They are resolved at run-time and do not require re-compilation of the PPI.

**Parameters:**

| Parameter      | Type   | Description                                                                                        |
| -------------- | ------ | -------------------------------------------------------------------------------------------------- |
| name           | string | The name of the `gbif` function to call.                                                             |
| arg1, arg2 ... | varies | The arguments to pass to the `gbif` function. GBIFs support a fixed or variable number of arguments. |

**Additional information:**

1. GBIFs are compiled into DLL(s) and support a fixed or variable number of arguments.
2. A separate dynamic link library called `gbif_util` contains `gbif` related functions and provides a modularised interface for OEMs wanting to implement BIFs.
3. Use for all application BIFs where possible.

**Example:**

```
gbif("whex_eff_update", 3, &fv0)
```

Calls the application-defined `gbif` named "whex_eff_update", passing the integer 3 and the address of fv0 as arguments.

**See Also:** `gbif_unlink`

### `gbif_unlink`

Removes all General Purpose Built-In Functions from memory.

**Syntax:**

```
gbif_unlink()
```

**Description:**

Removes every General Purpose Built-In Function (`gbif`) from the `gbif` table, unloading each library that provides them. It is called automatically when the interpreter shuts down.

**Example:**

```
gbif_unlink()
```

Removes all currently linked GBIFs, unloading the libraries that provide them.

**See Also:** `gbif`

### `get_max_pos`

Returns the maximum position limit of an axis.

**Syntax:**

```
float get_max_pos(integer axis_num)
```

**Description:**

Returns the upper (maximum) machine-frame position limit for the given axis. On SCARA machines, if the axis is not permitted to move in the positive direction the current position is returned instead of the configured limit. On non-SCARA machines the function returns LONG_MAX, indicating no meaningful limit is available.

**Parameters:**

| Parameter  | Type    | Description                      |
| ---------- | ------- | -------------------------------- |
| axis_num | integer | The 1-based axis index to query. |

**Returns:**

| Type  | Description                                                                                           |
| ----- | ----------------------------------------------------------------------------------------------------- |
| float | The maximum position limit for the axis in the machine frame. Returns LONG_MAX on non-SCARA machines. |

**Example:**

```
fv1 = get_max_pos(1)
```

Reads the maximum position limit of axis 1 into floating-point variable `fv1`.

**See Also:** `get_min_pos`

### `get_min_pos`

Returns the minimum position limit of an axis.

**Syntax:**

```
float get_min_pos(integer axis_num)
```

**Description:**

Returns the lower (minimum) machine-frame position limit for the given axis. On SCARA machines, if the axis is not permitted to move in the negative direction the current position is returned instead of the configured limit. On non-SCARA machines the function returns LONG_MIN, indicating no meaningful limit is available.

**Parameters:**

| Parameter  | Type    | Description                      |
| ---------- | ------- | -------------------------------- |
| axis_num | integer | The 1-based axis index to query. |

**Returns:**

| Type  | Description                                                                                           |
| ----- | ----------------------------------------------------------------------------------------------------- |
| float | The minimum position limit for the axis in the machine frame. Returns LONG_MIN on non-SCARA machines. |

**Example:**

```
fv1 = get_min_pos(1)
```

Reads the minimum position limit of axis 1 into floating-point variable fv1.

**See Also:** `get_max_pos`

### `H`

Selects a tool offset group.

**Syntax:**

```
H group_number
H(expression)
```

**Description:**

Selects a particular tool offset group from the tool table. Adjusts the tool offset transformation and sets up cutter radius compensation radius.

**Parameters:**

| Parameter    | Type       | Description                        |
| ------------ | ---------- | ---------------------------------- |
| group_number | integer    | Tool offset group number (0-99)    |
| expression   | expression | Expression evaluating to group number |

**Additional information:**

1. H-Code contains internal `sync` command.
2. Breaks program, path compensation, and velocity lookahead.
3. H0 clears all tool offsets to zero.
4. Performs the same fuction as [D](#d)

**Example:**

```
H6              { selects tool offset group 6 }
tooloffset(fv3) { selects group referred to by fv3 }
H0              { clears all tool offsets to zero }
```

Selects tool offset group 6, then selects the group referenced by `fv3`, and finally clears all tool offsets with `H0`.

**See Also:** `tooloffset`, `toolselect`, `eff`, `D`

### `hpp`

Obsolete Command.

**Description:**

Under the CiA402 standard, the servo-drive controls the homing sequence and the change of reference frame, so this command is no longer required.

### `indexpc`

Obsolete Command.

**Description:**

Under the CiA402 standard, the servo-drive controls the homing sequence and the change of reference frame, so this command is no longer required.

### `indexpcoff`

Obsolete Command.

**Description:**

Under the CiA402 standard, the servo-drive controls the homing sequence and the change of reference frame, so this command is no longer required.

### `joint`

Moves an individual joint to a specified position.

**Syntax:**

```
joint joint_number, position
```

**Description:**

Moves an individual joint to a specified position. Most often used in homing operations.

**Parameters:**

| Parameter    | Type    | Description                                       |
| ------------ | ------- | ------------------------------------------------- |
| joint_number | integer | Joint number (1-48)     |
| position     | float   | Target absolute joint position (mm or degrees)    |

**Additional information:**

1. Target position is always absolute and must be in metric.
2. Positions in mm for prismatic joints, degrees for revolute joints.
3. Feedrate defined by `feedrate` word.
4. Soft axes are also allocated joints (soft joints).

**Example:**

```
joint 5, 0    { Move joint 5 to position 0 }
```

Moves joint 5 to absolute position 0, as is typically done during a homing sequence.

**See Also:** `axis`, `machineon`

### `jointmpg`

Moves a joint under manual pulse generator (MPG) control until a stop condition is satisfied.

**Syntax:**

```
jointmpg joint_num stopif variable
jointmpg joint_num stopifnot variable
```

**Description:**

Commands the joint identified by joint_num to move under manual pulse generator (MPG) control. The move terminates on a boolean stop condition: with `stopif` the motion stops when variable becomes true, and with `stopifnot` the motion stops when variable becomes false.

**Parameters:**

| Parameter | Type    | Description                                                                                                               |
| --------- | ------- | ------------------------------------------------------------------------------------------------------------------------- |
| joint_num | integer | The joint number to move under MPG control.                                                                               |
| variable  | boolean | The boolean stop-condition variable evaluated to terminate the move (`stopif` stops when true, `stopifnot` stops when false). |

**Example:**

```
jointmpg 5 stopif (plc)bv200
```

Puts joint 5 under manual pulse generator control. The operator jogs the joint with the handwheel and the move terminates when the PLC boolean variable (plc)bv200 becomes true.

**See Also:** `axismpg`, `joint`

### `log`

Returns the natural logarithm (base e) of the expression.

**Syntax:**

```
float log(float expr)
```

**Description:**

Return the natural logarithm (base e) of the expression `expr`.

**Parameters:**

| Parameter | Type  | Description           |
| --------- | ----- | --------------------- |
| expr      | float | Value (must be > 0)   |

**Returns:**

| Type  | Description                    |
| ----- | ------------------------------ |
| float | The natural logarithm of expr  |

**Additional information:**

1. The expression `expr` must be greater than 0.

**Example:**

```
fv1 = log(2.0)
```

Assigns the natural logarithm of 2.0 (approximately 0.6931) to floating-point variable `fv1`.

**See Also:** `exp`

### `logten`

Returns the common logarithm (base 10) of the expression.

**Syntax:**

```
float logten(float expr)
```

**Description:**

Return the common logarithm (base 10) of the expression `expr`.

**Parameters:**

| Parameter | Type  | Description           |
| --------- | ----- | --------------------- |
| expr      | float | Value (must be > 0)   |

**Returns:**

| Type  | Description                  |
| ----- | ---------------------------- |
| float | The base 10 logarithm of expr |

**Additional information:**

1. The expression `expr` must be greater than 0.

**Example:**

```
fv1 = logten(2.0)
```

Assigns the base-10 logarithm of 2.0 (approximately 0.3010) to floating-point variable `fv1`.

**See Also:** `expten`

### `logtwo`

Returns the logarithm (base 2) of the expression.

**Syntax:**

```
float logtwo(float expr)
```

**Description:**

Return the logarithm (base 2) of the expression `expr`.

**Parameters:**

| Parameter | Type  | Description           |
| --------- | ----- | --------------------- |
| expr      | float | Value (must be > 0)   |

**Returns:**

| Type  | Description                 |
| ----- | --------------------------- |
| float | The base 2 logarithm of expr |

**Additional information:**

1. The expression `expr` must be greater than 0.

**Example:**

```
fv1 = logtwo(10.0)
```

Assigns the base-2 logarithm of 10.0 (approximately 3.3220) to floating-point variable `fv1`.

**See Also:** `exptwo`

### `machineon`

Enables or re-enables servo control of the machine.

**Syntax:**

```
machineon
```

**Description:**

Enables or re-enables servo control of the machine. Required after power on, emergency stop, returning a spindle to servo'd joint control, and soft limit overtravel.

**Additional information:**

1. When XILB201-212 bits are reset, joint enters tracking mode. `machineon` must be programmed to resume servo control.
2. Contains internal sync command.
3. Latches current feedback position into command position.
4. Should be used cautiously in part programs (usually effected by reset button).

**Example:**

```
machineon
```

Re-enables servo control of the machine, for example after an emergency stop or power-on, before motion is resumed.

**See Also:** `joint`, `reprimecp`

### `mod`

Returns the fractional part of the expression.

**Syntax:**

```
float mod(float expr)
```

**Description:**

Return the fractional part of the expression `expr`.

**Parameters:**

| Parameter | Type  | Description                        |
| --------- | ----- | ---------------------------------- |
| expr      | float | Value to extract fractional part from |

**Returns:**

| Type  | Description                      |
| ----- | -------------------------------- |
| float | The fractional part of the value |

**Example:**

```
fv1 = mod(-54.0992)
```

Assigns the fractional part of -54.0992 (that is, -0.0992) to floating-point variable `fv1`.

**See Also:** `trunc`

### `open`

Opens a disk file for reading or writing.

**Syntax:**

```
open(&stream, filename, mode)
```

**Description:**

Opens disk files for reading or writing data.

**Parameters:**

| Parameter | Type   | Description                                                               |
| --------- | ------ | ------------------------------------------------------------------------- |
| &stream   | stream | File identifier (unique name for future operations)                       |
| filename  | string | File name. Relative paths are relative to initial power up directory.    |
| mode      | mode   | `input` (read), `output` (write, deletes existing), or `append` (write, appends) |

**Additional information:**

1. Files opened in `output`/`append` mode should be closed ASAP.
2. All files closed automatically when program completes/rewinds/deactivates.
3. File state maintained in lookahead.

**Example:**

```
open(&dfile_1, "/tmp/dfile.dout", output)
open(&dfile_2, "data/input.dat", input)
```

Opens `/tmp/dfile.dout` for writing (creating or truncating it) as stream `dfile_1`, and opens `data/input.dat` for reading as stream `dfile_2`.

**See Also:** `close`, `read`, `write`

### `oscillate`

Starts one axis oscillating immediately using a trapezoidal profile.

**Syntax:**

```
oscillate(string dimension_string, float amplitude, float feedrate, float offset_shift, float dwell_neg, float dwell_pos)
```

**Description:**

This function is used to start one axis oscillating immediately. The trapezoidal oscillator simply moves from one position to the next and back, with a variable pause (a dwell) at either end, so that a graph of position versus time resembles a trapezoid.

**Parameters:**

| Parameter        | Type   | Description                                                             |
| ---------------- | ------ | ----------------------------------------------------------------------- |
| dimension_string | string | The axis to oscillate.                                                  |
| amplitude        | float  | The magnitude of the movement from peak to peak.                        |
| feedrate         | float  | The maximum velocity the oscillator should attain during its motion.    |
| offset_shift     | float  | Shifts the centre of the oscillation to another point on the same axis. |
| dwell_neg        | float  | Dwell time at the negative end of the oscillation.                      |
| dwell_pos        | float  | Dwell time at the positive end of the oscillation.                      |

**Example:**

```
oscillate("X", 10, 500, 0, 0.1, 0.1)
```

Oscillates the X axis with a peak-to-peak amplitude of 10 at a maximum feedrate of 500, with no offset shift and a 0.1 dwell at each end.

**See Also:** `oscillate_init`, `oscillate_sine`, `oscillate_end`, `oscillate_end_all`, `oscillate_start_all`

### `oscillate_end`

Stops oscillations on a single axis.

**Syntax:**

```
oscillate_end(string dimension_string)
```

**Description:**

Stops the oscillations on a single axis.

**Parameters:**

| Parameter        | Type   | Description                     |
| ---------------- | ------ | ------------------------------- |
| dimension_string | string | The axis dimension to stop      |

**Additional information:**

1. `oscillate_end()` is NOT synchronized. The axis motion may continue for a time after this call. In particular, a sinusoidal oscillator may take a significant time to come to a smooth halt.
2. Use `oscillate_end_all()` in preference -- this call IS synchronized.

**Example:**

```
oscillate_end("X")
```

Stops the oscillation on the X axis. Because this call is not synchronised, motion may continue briefly; prefer `oscillate_end_all()` where the program must wait for motion to stop.

**See Also:** `oscillate_end_all`, `oscillate`, `oscillate_sine`

### `oscillate_end_all`

Stops oscillations on all axes.

**Syntax:**

```
oscillate_end_all()
```

**Description:**

Stops oscillations on all axes, regardless of which way they were begun. This call IS synchronized -- the next line in the Part Program is not executed until motion has stopped.

**Example:**

```
oscillate_end_all()
```

Stops oscillation on every axis and does not return until all oscillator motion has stopped.

**See Also:** `oscillate_end`, `oscillate`, `oscillate_sine`

### `oscillate_init`

Prepares trapezoidal oscillation parameters on a single axis without starting.

**Syntax:**

```
oscillate_init(string dimension_string, float amplitude, float feedrate, float offset_shift, float dwell_neg, float dwell_pos)
```

**Description:**

The init function is used to set the parameters for oscillation on a single axis. The EPPL programmer must call the `oscillate_start_all()` function afterwards.

**Parameters:**

| Parameter        | Type   | Description                                          |
| ---------------- | ------ | ---------------------------------------------------- |
| dimension_string | string | The axis dimension to oscillate                      |
| amplitude        | float  | The magnitude of the movement from peak to peak      |
| feedrate         | float  | The maximum velocity the oscillator should attain    |
| offset_shift     | float  | Shifting the centre of the oscillation to another point on the same axis |
| dwell_neg        | float  | Dwell time at negative end of oscillation            |
| dwell_pos        | float  | Dwell time at positive end of oscillation            |

**Example:**

```
oscillate_init("X", 10, 500, 0, 0.1, 0.1)
oscillate_start_all()
```

Prepares a trapezoidal oscillation on the X axis (peak-to-peak amplitude 10, maximum feedrate 500, no offset shift and a 0.1 dwell at each end); the motion begins when `oscillate_start_all()` is called.

**See Also:** `oscillate`, `oscillate_start_all`, `oscillate_end`, `oscillate_end_all`

### `oscillate_init_freq_sine`

Prepares sinusoidal oscillation parameters on an axis specifying frequency rather than maximum velocity.

**Syntax:**

```
oscillate_init_freq_sine(string axis_name, float amplitude, float frequency, float initial_phase)
```

**Description:**

Prepares sinusoidal oscillation parameters specifying oscillation frequency rather than maximum velocity. Added for completeness alongside `oscillate_init_freq_sync`.

**Parameters:**

| Parameter     | Type   | Description                                          |
| ------------- | ------ | ---------------------------------------------------- |
| axis_name     | string | The axis name to oscillate                           |
| amplitude     | float  | Peak-to-peak amplitude                               |
| frequency     | float  | Oscillation frequency (Hz)                           |
| initial_phase | float  | Phase angle at current (starting) position           |

**Example:**

```
oscillate_init_freq_sine("X", 10, 5, 0)
oscillate_start_all()
```

Prepares a sinusoidal oscillation on the `X` axis with a peak-to-peak amplitude of 10 at a frequency of 5 Hz, starting from zero phase; the motion begins when `oscillate_start_all()` is called.

**See Also:** `oscillate_init_sine`, `oscillate_init_freq_sync`, `oscillate_start_all`

### `oscillate_init_freq_sync`

Prepares synchronous oscillation parameters on an axis specifying frequency rather than maximum velocity.

**Syntax:**

```
oscillate_init_freq_sync(string axis_name, float amplitude, float frequency, float initial_phase)
```

**Description:**

Alternative initialization for synchronous oscillation: specify oscillation frequency rather than maximum velocity.

**Parameters:**

| Parameter     | Type   | Description                                          |
| ------------- | ------ | ---------------------------------------------------- |
| axis_name     | string | The axis name to oscillate                           |
| amplitude     | float  | Peak-to-peak amplitude                               |
| frequency     | float  | Oscillation frequency (Hz)                           |
| initial_phase | float  | Phase angle at current (starting) position           |

**Example:**

```
oscillate_init_freq_sync("U", 100, 5, 315)
oscillate_init_freq_sync("W", 100, 5, 45)
oscillate_start_all()
```

Prepares a synchronous sinusoidal oscillation across the `U` and `W` axes, specifying frequency (5 Hz) rather than maximum velocity; the axes begin their Lissajous motion when `oscillate_start_all()` is called.

**See Also:** `oscillate_init_sync`, `oscillate_init_freq_sine`, `oscillate_start_all`

### `oscillate_init_sine`

Prepares sinusoidal oscillation parameters on an axis without starting.

**Syntax:**

```
oscillate_init_sine(string dimension, float amplitude, float maximum_feedrate, float offset_shift)
```

**Description:**

This prepares the oscillation parameters on the specified axis. It will not begin until `oscillate_start_all()` is run.

**Parameters:**

| Parameter         | Type   | Description                                          |
| ----------------- | ------ | ---------------------------------------------------- |
| dimension         | string | The axis dimension to oscillate                      |
| amplitude         | float  | The magnitude of the movement from peak to peak      |
| maximum_feedrate  | float  | The maximum velocity the oscillator should attain    |
| offset_shift      | float  | Shifting the centre of the oscillation to another point on the same axis |

**Example:**

```
oscillate_init_sine("U", 100, 2000, 0)
oscillate_start_all()
```

Prepares a sinusoidal oscillation on the `U` axis with a peak-to-peak amplitude of 100 and a maximum feedrate of 2000, centred on the current position, then starts it with `oscillate_start_all()`.

**See Also:** `oscillate_sine`, `oscillate_start_all`, `oscillate_end`, `oscillate_end_all`

### `oscillate_init_sync`

Prepares synchronous oscillation parameters on an axis without starting.

**Syntax:**

```
oscillate_init_sync(string axis_name, float amplitude, float max_velocity, float initial_phase)
```

**Description:**

Initialize a synchronous oscillator on the specified axis. Synchronous oscillation occurs between 2 or more axes simultaneously, with synchronization between the oscillation axes. It creates a "Lissajous pattern" type of motion in the plane/volume defined by the oscillator axes.

The phase of the oscillation is that of the COSINE wave of the normal operating motion. i.e. maximum amplitude at 0 and 2*pi, zero amplitude at pi/2 and 3*pi/2, minimum amplitude at pi, etc.

**Parameters:**

| Parameter     | Type   | Description                                          |
| ------------- | ------ | ---------------------------------------------------- |
| axis_name     | string | The axis name to oscillate                           |
| amplitude     | float  | Peak-to-peak amplitude                               |
| max_velocity  | float  | Axis maximum velocity                                |
| initial_phase | float  | Phase angle at current (starting) position           |

**Additional information:**

1. Only existing axes (hard or soft) are able to oscillate. (that is, no arbitrary oscillation vectors).
2. Synchronization is only between the specified oscillators and not any other motions.
3. Synchronous Oscillations is an extension of the Sinusoidal Oscillation mode, and uses the same live offset mechanism.
4. Only sinusoidal profile oscillation is supported.
5. The oscillating axes must be halted prior to the command to start oscillation (`oscillate_start_all()`) being given.


**Example:**

```
oscillate_init_sync("U", 100, 2000, 315)
oscillate_init_sync("W", 100, 2000, 45)
oscillate_start_all()
```

Prepares synchronous oscillation on the `U` and `W` axes (both peak-to-peak amplitude 100, maximum velocity 2000) at starting phases of 315 and 45 degrees, then starts both together with `oscillate_start_all()` to trace a Lissajous pattern.

**See Also:** `oscillate_init_freq_sync`, `oscillate_start_all`, `oscillate_end`, `oscillate_end_all`

### `oscillate_sine`

Starts sinusoidal oscillation on an axis immediately.

**Syntax:**

```
oscillate_sine(string dimension, float amplitude, float maximum_feedrate, float offset_shift)
```

**Description:**

This function will begin a sinusoidal oscillation on the axis specified. The oscillation will begin immediately.

**Parameters:**

| Parameter         | Type   | Description                                          |
| ----------------- | ------ | ---------------------------------------------------- |
| dimension         | string | The axis dimension to oscillate                      |
| amplitude         | float  | The magnitude of the movement from peak to peak      |
| maximum_feedrate  | float  | The maximum velocity the oscillator should attain    |
| offset_shift      | float  | Shifting the centre of the oscillation to another point on the same axis |

**Example:**

```
oscillate_sine("U", 100, 2000, 0)
```

Immediately starts a sinusoidal oscillation on the `U` axis with a peak-to-peak amplitude of 100 and a maximum feedrate of 2000, centred on the current position.

**See Also:** `oscillate_init_sine`, `oscillate_end`, `oscillate_end_all`

### `oscillate_start_all`

Starts all prepared oscillators.

**Syntax:**

```
oscillate_start_all()
```

**Description:**

This function tells all oscillators to begin oscillating. If any oscillators are prepared (via init) or already oscillating, they will be oscillating after this method.

**Example:**

```
oscillate_init_sine("U", 100, 2000, 0)
oscillate_init_sine("V", 100, 2000, 0)
oscillate_start_all()
```

Prepares sinusoidal oscillations on the `U` and `V` axes and then starts them together with a single call to `oscillate_start_all()`.

**See Also:** `oscillate_init`, `oscillate_init_sine`, `oscillate_init_sync`, `oscillate_end_all`

### `posnlatch`

Stores the current commanded machine position.

**Syntax:**

```
posnlatch
```

**Description:**

Stores the current commanded machine position. The position in three different reference frames is stored (joint, machine, and user). Each frame is stored as an array of dimension and numerical float variables.

**System Variables Updated:**

| Variable          | Description                  |
| ----------------- | ---------------------------- |
| `g_posn_jf`[0..47]  | Joint frame positions        |
| `g_posn_pf`[0..47]  | Physical frame positions |
| `g_posn_mf`[0..47]  | Machine frame positions      |
| `g_posn_uf`[0..47]  | User frame positions         |

**Additional information:**

1. All linear axis/joint values stored in `metric` (mm).
2. All rotational axis/joint values stored in degrees.
3. Use `unitcv()` when accessing stored positions.
4. This command breaks lookahead.

**Example:**

```
sub shiftmachine
  posnlatch { Break lookahead and remember position }
  if g_posn_jf[1] < 250.0 then
    linear X(unitcv(g_posn_uf[0]) + 20)
    fv1 = X
  ifend
subend
```

Latches the current machine position (breaking lookahead) and, if joint 1's latched position is below 250 mm, performs a linear move to the stored user-frame position plus 20.

**See Also:** `probelatch`, `unitcv`

### `pow`

Returns the value of base raised to the exponent power.

**Syntax:**

```
float pow(float base_expr, float exp_expr)
```

**Description:**

Return the value of `base_expr` raised to the `exp_expr` power.

**Parameters:**

| Parameter | Type  | Description       |
| --------- | ----- | ----------------- |
| base_expr | float | The base value    |
| exp_expr  | float | The exponent      |

**Returns:**

| Type  | Description                     |
| ----- | ------------------------------- |
| float | base_expr raised to exp_expr power |

**Additional information:**

1. A domain error will occur if `base_expr` is 0 and `exp_expr` is ≤ 0.
2. A domain error will occur if `base_expr` is < 0 and `exp_expr` has a fractional part.

**Example:**

```
fv1 = pow(1.5, 2.5)
```

Raises 1.5 to the power of 2.5 (approximately 2.7556) and stores the result in floating-point variable `fv1`.

**See Also:** `sqrt`, `exp`

### `probe_reenable`

Reinitializes the probe between probing operations.

**Syntax:**

```
probe_reenable()
probe_reenable(polarity)
```

**Description:**

Used in probing part programs to reinitialize the probe between probing operations. For example, in digitizing cycles requiring many probe touches, this is called between each touch.

**Parameters:**

| Parameter | Type    | Description                                               |
| --------- | ------- | --------------------------------------------------------- |
| polarity  | integer | (Optional) 0 = falling edge, 1 = rising edge. Uses current polarity if omitted. |

**Returns:**

| Value | Description                              |
| ----- | ---------------------------------------- |
| 0     | Success                                  |
| !0    | Probe is already in a triggered state    |

**Additional information:**

1. When successful, XOLB_ACTIVATE_PROBE set to `on`, and `off` when probe triggers.

**Example:**

```
probe_reenable(1)     { Reinitialize for rising-edge triggering }
```

Reinitializes the probe with rising-edge triggering.

**See Also:** `probing_begin`, `probing_end`, `probelatch`

### `probelatch`

Transforms stored probe position into machine and user frames.

**Syntax:**

```
probelatch
```

**Description:**

Transforms the stored machine joint position at the time of a measurement interrupt into machine and user frames. Loads all variables associated with probing from digital servo drives into shared memory variables.

The probe position stored in the drive can originate from one of two SERCOS parameters: ID130 for positive edge probing and ID131 for negative edge probing. These values must be transferred cyclically from the drive to the CNC. `probelatch` establishes the current polarity and reads the appropriate cyclic value (ID130 or ID131) into G_PROBED_JFx. Once the joint values are latched for all drives, the transformations to machine and user frame can be performed.

**System Variables Updated:**

| Variable            | Description                    |
| ------------------- | ------------------------------ |
| `g_probed_jf`[0..47]  | Joint frame probed positions   |
| g_probed_pf[0..47]  | Physical frame probed positions |
| `g_probed_mf`[0..47]  | Machine frame probed positions |
| `g_probed_uf`[0..47]  | User frame probed positions    |

**Additional information:**

1. All linear values stored in `metric` (mm); use `unitcv()` to access.
2. Rotational values stored in degrees.
3. This command breaks all lookahead.
4. Should be used with probing operations.

**Example:**

```
probelatch
fv1 = g_probed_uf[2]
```

Transforms the latched probe position into machine and user frames, then reads the probed `Z` user-frame position into `fv1`.

**See Also:** `posnlatch`, `probing_begin`, `probing_end`

### `probing_begin`

Initializes machine for probing.

**Syntax:**

```
probing_begin()
probing_begin(polarity)
```

**Description:**

Initializes machine for probing. Polarity can be 0 (falling edge) or 1 (rising edge). Uses last polarity if no argument supplied.

**Parameters:**

| Parameter | Type    | Description                              |
| --------- | ------- | ---------------------------------------- |
| polarity  | integer | (Optional) 0 = falling edge, 1 = rising edge |

**Returns:**

| Value | Description                              |
| ----- | ---------------------------------------- |
| 0     | Success                                  |
| !0    | Probe is already in a triggered state    |

**Additional information:**

1. Polarity persists until changed by `probing_begin()` or `probe_reenable()`.
2. `probing_end()` must be called before `probing_begin()` can be called again.
3. When successful, XOLB_ACTIVATE_PROBE set to `on`.

**Example:**

```
probing_begin(1)     { Initialize probing for rising-edge triggering }
```

Initializes the machine for probing with rising-edge triggering.

**See Also:** `probing_end`, `probe_reenable`, `probelatch`

### `probing_end`

Indicates that probing is complete.

**Syntax:**

```
probing_end()
```

**Description:**

Used to indicate that probing is complete and inform drives not to expect to latch a machine position due to probe triggering.

**Example:**

```
sub exit
  write("\n probe interference Probe already touching\n")
  probing_end()
subend
```

Reports that the probe is already touching and then calls `probing_end()` to end probing.

**See Also:** `probing_begin`, `probe_reenable`

### `pseudooff`

Switches pseudo movement mode off.

**Syntax:**

```
pseudooff
```

**Description:**

Switches pseudo movement mode off. Following movement blocks will be performed normally. If CNC was in `pseudoon` mode before this command, the CNC will be in a state as if it had actually performed the moves between `pseudoon` and `pseudooff`.

**Additional information:**

1. The last move of the `pseudoon` section must end at the same position where `pseudoon` was issued.
2. May not program discontinuities in path.
3. Cancel lookahead will cause `pseudoon` mode to be cancelled.
4. `pseudooff` does not contain an internal sync - be careful of lookahead.

**Example:**

```
pseudoon
N1 mlinear X(unitcv(-10000))
N2 X(unitcv(g_posn_mf[0]))
pseudooff
```

Enters pseudo mode, performs remembered (not physically executed) moves, and returns to normal movement with `pseudooff`, ending at the position where `pseudoon` was issued.

**See Also:** `pseudoon`

### `pseudoon`

Switches pseudo movement mode on.

**Syntax:**

```
pseudoon
```

**Description:**

Switches pseudo movement mode on. Waits for machine to stop, saves current machine position, then enters pseudo mode. All following movement blocks until `pseudooff` will be remembered but **not performed** by the CNC.

**Example:**

```
sub x_axis_mpg
  F0
  (plc)bv200 = on
  posnlatch
  pseudoon
  N1 mlinear X(unitcv(-10000))
  N2 X(unitcv(g_posn_mf[0])) stopifnot (plc)bv200
  if (plc)bv200 = off goto N10
  pseudooff
  N3 X(unitcv(10000)) stopifnot (plc)bv200
  N10 sync
subend
```

Latches the current position, enters pseudo mode so the MPG jog moves are remembered but not physically executed, and leaves pseudo mode with `pseudooff` before the following real move.

**See Also:** `pseudooff`, `posnlatch`

### `random`

Returns a pseudorandom integer.

**Syntax:**

```
integer random(integer seed)
```

**Description:**

The `random()` function returns a pseudorandom integer in the range 0 to 32767.

For seed = 0, the underlying C function `rand()` is called immediately. A non-zero seed will be passed to the C library `srand()` function prior to calling `rand()`. This changes the behaviour of `rand()` as follows:

To reinitialize the generator, use 1 as the seed argument. Any other value for seed sets the generator to a random starting point. Calling `rand` before any call to `srand` generates the same sequence as calling `srand` with seed passed as 1.

**Parameters:**

| Parameter | Type    | Description                                          |
| --------- | ------- | ---------------------------------------------------- |
| seed      | integer | 0 to call `rand()` directly, non-zero to seed the generator first |

**Returns:**

| Type    | Description                              |
| ------- | ---------------------------------------- |
| integer | A pseudorandom integer in the range 0 to 32767 |

**Example:**

```
iv1 = random(1)
iv2 = mod(random(0), 6)
```

Reinitializes the generator with a seed of 1, then uses `mod` to reduce the next pseudorandom value to the range 0 to 5.

**See Also:** `mod`

### `read`

Reads data from a file or `keyboard`.

**Syntax:**

```
read(&variable)
read(stream, &variable)
```

**Description:**

Inputs data as a string and converts to the appropriate data type (Boolean, integer, float, or string).

**Parameters:**

| Parameter | Type     | Description                                        |
| --------- | -------- | -------------------------------------------------- |
| stream    | stream   | (Optional) Stream identifier (defaults to `keyboard`) |
| &variable | variable | Variable to hold read data. Must be initialized if local. |

**Returns:**

| Value      | Description          |
| ---------- | -------------------- |
| `read_ok`    | Success              |
| READ_EOF   | End of file reached  |
| `read_error` | Error occurred       |

**Additional information:**

1. The "&" symbol must be programmed before the variable name.
2. CNC will wait for data and will NOT respond to events while waiting.

**Example:**

```
open("C:/tg7/pp/data.txt", "r", &fstream)
read(fstream, &fv1)
close(fstream)
```

Opens a file for reading, reads one value into `fv1`, then closes the file.

**See Also:** `open`, `write`, `readkey`, `close`

### `readkey`

Reads a single character.

**Syntax:**

```
readkey(&variable)
readkey(stream, &variable)
readkey(stream, &variable, timeout)
```

**Description:**

Single character input, one character at a time.

**Parameters:**

| Parameter | Type     | Description                                        |
| --------- | -------- | -------------------------------------------------- |
| stream    | stream   | (Optional) Stream identifier (defaults to `keyboard`) |
| &variable | string   | String variable to hold the character              |
| timeout   | float    | (Optional) Timeout in seconds                      |

**Returns:**

| Value      | Description              |
| ---------- | ------------------------ |
| Positive   | Success (character read) |
| READ_EOF   | End of file reached      |
| `read_tmout` | Timeout expired          |
| `read_error` | Error occurred           |

**Additional information:**

1. The "&" symbol must be programmed before the variable name.
2. `readkey`() does not echo the character to `vdu`.
3. Cannot be used to read PLC and front panel switches.

**Example:**

```
readkey(keyboard, &sv1, 5)  { Wait up to 5 seconds for a key }
```

Reads a single character from the keyboard up to five seconds before timing out.

**See Also:** `read`, `write`

### `reprimecp`

Re-enables CNC control after drive-controlled moves.

**Syntax:**

```
reprimecp
reprimecp joint_number
```

**Description:**

Re-enables CNC control after some kinds of drive controlled moves, where joint motion has occurred outside the CNC's direct control. Forces the actual position reported by a drive to equal the command position.

**Parameters:**

| Parameter    | Type    | Description                                    |
| ------------ | ------- | ---------------------------------------------- |
| joint_number | integer | (Optional) Specific joint to reprime. Reprimes all if omitted. |

**Additional information:**

1. Will wait until drive(s) have stopped moving (within tolerance).
2. If tolerance too large or joint moving erratically, joint "creep" can occur.
3. **Do not use unless absolutely necessary.**
4. **Machine absolute position (Home position) can be lost.**

**Example:**

```
reprimecp 3
```

Reprimes only joint 3.

**See Also:** `machineon`, `sgsc`

### `restore_vpi_defaults`

Restores the VPI database parameters to their default values.

**Syntax:**

```
restore_vpi_defaults()
```

**Description:**

Reloads the default values for the VPI database parameters, discarding any run-time changes previously made through the database access functions.

**Example:**

```
restore_vpi_defaults()
```

Restores every VPI database parameter to its default value.

**See Also:** `dba_put_float_parm`, `dba_get_float_parm`

### `restoremodal`

Restores saved modal conditions.

**Syntax:**

```
restoremodal
```

**Description:**

Restores the modal conditions saved at the previous `savemodal` instruction. Used when exiting a subprogram to restore modal conditions to their original values.

**Additional information:**

1. `savemodal` and `restoremodal` may **not** be nested.
2. Will not save or restore values (e.g., current feedrate setting).
3. G-Codes with complex mode swapping rules may not restore properly.

**Example:**

```
savemodal
metric
G1 X100 Y100
restoremodal
```

Saves the modal state, switches to metric for a move, then restores the previously saved modal conditions with `restoremodal`.

**See Also:** `savemodal`

### `round`

Returns the closest integer value to the expression.

**Syntax:**

```
float round(float expr)
```

**Description:**

Return the closest integer value to the expression `expr`. Return this value as a float type.

**Parameters:**

| Parameter | Type  | Description      |
| --------- | ----- | ---------------- |
| expr      | float | Value to round   |

**Returns:**

| Type  | Description                              |
| ----- | ---------------------------------------- |
| float | The rounded value (as a float type)      |

**Additional information:**

1. Returns float type, not integer.

**Example:**

```
fv1 = round(1.01)
fv2 = round(1.99)
fv3 = round(-1.01)
fv4 = round(-1.99)
```

Rounds each value to the nearest integer, returned as a float: 1.01 gives 1, 1.99 gives 2, -1.01 gives -1 and -1.99 gives -2.

**See Also:** `trunc`

### `rtod`

Converts radians to degrees.

**Syntax:**

```
float rtod(float expr)
```

**Description:**

Convert radians to degrees. The expression `expr` is assumed to be in units of radians.

**Parameters:**

| Parameter | Type  | Description        |
| --------- | ----- | ------------------ |
| expr      | float | Angle in radians   |

**Returns:**

| Type  | Description            |
| ----- | ---------------------- |
| float | The angle in degrees   |

**Example:**

```
fv1 = rtod(2.0)
```

Converts 2.0 radians to degrees (approximately 114.591) and stores the result in `fv1`.

**See Also:** `dtor`

### `runout_comp`

Enables runout compensation.

**Syntax:**

```
runout_comp(profile_device_id, number_of_joints, number_of_compensation_points, ref_joint, joint_a, ...)
```

**Description:**

Enables runout compensation, typically used to compensate for a slightly off-centre tool. The reference joint is usually a rotary axis and one or more joints can be compensated based on its position.

**Parameters:**

| Parameter                   | Type    | Description                                      |
| --------------------------- | ------- | ------------------------------------------------ |
| profile_device_id           | integer | ID of profile device containing lookup table     |
| number_of_joints            | integer | Number of joints to compensate                   |
| number_of_compensation_points | integer | Number of rows in lookup table (max 360)       |
| ref_joint                   | integer | Reference joint number                           |
| joint_a, ...                | integer | List of joints to be compensated                 |

**Example:**

```
F1000
joint 4,0
g_iv115 = tg_prof_alloc(5,2)
tg_prof_write(g_iv115, 0, 0.0, 0)
tg_prof_write(g_iv115, 90, 0.1, 1)
tg_prof_write(g_iv115, 180, 0.05, 2)
tg_prof_write(g_iv115, 270, 0.1, 3)
tg_prof_write(g_iv115, 360, 0.0, 4)
runout_comp(g_iv115, 1, 5, 4, 1)
tg_prof_free(g_iv115)
joint 4,360
```

Builds a five-point runout compensation lookup table in a profile device, enables runout compensation for joint 1 referenced to rotary joint 4, then frees the profile device and rotates joint 4 through 360 degrees.

**See Also:** `runout_comp_cancel`, `centre_comp`, `tg_prof_alloc`

### `runout_comp_cancel`

Cancels runout compensation.

**Syntax:**

```
runout_comp_cancel()
```

**Description:**

Cancels runout compensation that was activated by `runout_comp`.

**Example:**

```
runout_comp_cancel()
```

Cancels the runout compensation previously activated by `runout_comp`.

**See Also:** `runout_comp`

### `savemodal`

Saves the current modal conditions.

**Syntax:**

```
savemodal
```

**Description:**

Saves the current modal conditions. Used when entering a subprogram to save modal state before modifying it.

**Additional information:**

1. `savemodal` and `restoremodal` may **not** be nested.
2. Will not save or restore values (e.g., current feedrate setting).
3. Typically used to allow subprograms written in metric mode to work in inch mode.

**Example:**

```
savemodal
metric
initial_crc_mode = 40
if G41 initial_crc_mode = 41
if G42 initial_crc_mode = 42
G41
G1 X100 Y100
...
restoremodal
```

Saves the current modal state, switches to metric, records and applies the appropriate cutter radius compensation mode, performs a move, and later restores the original modal conditions with `restoremodal`.

**See Also:** `restoremodal`

### `select_active_probe`

Selects the active probe by index.

**Syntax:**

```
integer select_active_probe(integer probe_number)
```

**Description:**

Selects which configured probe is active for subsequent probing operations. Probes are numbered from 1. Returns the number of the newly selected probe, or 0 if the selection failed (for example, if probing is disabled for the part program or the argument is invalid).

**Parameters:**

| Parameter    | Type    | Description                              |
| ------------ | ------- | ---------------------------------------- |
| probe_number | integer | The 1-based index of the probe to make active |

**Returns:**

| Type    | Description                                     |
| ------- | ----------------------------------------------- |
| integer | The newly selected probe number, or 0 on failure |

**Example:**

```
iv1 = select_active_probe(2)
```

Makes probe 2 the active probe and stores the resulting probe number in `iv1`.

**See Also:** `probing_begin`, `probe_reenable`, `probelatch`

### `sglmc`

Synchronous Generic Logical Machine Command.

**Syntax:**

```
sglmc lm_num, cmd_number, cmd_value
```

**Description:**

Synchronous Generic Logical Machine Command - extends EPPL functionality without changing grammar/syntax. Allows addition of sub-commands that affect whole Logical Machines.

**Parameters:**

| Parameter  | Type    | Description                               |
| ---------- | ------- | ----------------------------------------- |
| lm_num     | integer | Always 1 (SGLMCs defined only for LM1)    |
| cmd_number | integer | Command identifier (see table)            |
| cmd_value  | varies  | Argument for sub-command                  |

**Command Numbers:**

| cmd_number | Description                                | Argument            |
| ---------- | ------------------------------------------ | ------------------- |
| 0          | Switch V-block mode off                    | 0                   |
| 1          | Switch V-block mode on                     | 0                   |
| 2          | Disable wheel spindle center line offsets  | 0                   |
| 3          | Enable wheel spindle center line offsets   | wheel spindle number |
| 4          | V-Block theta setting                      | theta               |
| 5          | LLX x' slave disable                       | 0                   |
| 6          | LLX x' slave enable                        | 0                   |
| 7          | TCG C Axis Offset for spindle/probe        | Offset in degrees   |
| 8          | PCC Bevel Head Kinematics `off`              | 0                   |
| 9          | PCC Bevel Head Kinematics `on`               | 0                   |
| 10         | TCG R Axis Offset                          | Offset in degrees   |

**Additional information:**

1. `sglmc` commands are **passive** - do not cause axis motion.
2. Positions will be updated to reflect changed offsets.

**Example:**

```
sglmc 1,7,-180
sglmc 1,7,0
sglmc 1,2,0
```

Sets the C-axis offset to -180 degrees, then cancels the C-axis offset, then cancels the spindle centre-line offsets.

**See Also:** `sgsc`

### `sgsc`

Synchronous Generic Servo Command.

**Syntax:**

```
sgsc expr1 [, expr2 [, expr3]]
```

**Description:**

Synchronous Generic Servo Command - sends miscellaneous data to the servo control sub-system of the CNC software.

**Parameters:**

| Parameter | Type    | Description                                    |
| --------- | ------- | ---------------------------------------------- |
| expr1     | integer | Command number                                 |
| expr2     | integer | (Optional) Joint number (set to 0 if not used) |
| expr3     | float   | (Optional) Data sent to servo controller       |

**Additional information:**

1. Causes an internal sync command to be executed first.
2. CNC software is placed in state allowing command/feedback positions to be modified.
3. `sgsc` is completed by "repriming" the CNC with feedback position.
4. Corresponding software must be present in CNC or error produced.

**Example:**

```
sgsc 12, 3, 0.5
```

Sends generic servo command 12 to joint 3 with a data value of 0.5, after an implicit internal sync.

**See Also:** `sglmc`, `reprimecp`

### `sin`

Returns the sine of the expression.

**Syntax:**

```
float sin(float expr)
```

**Description:**

Return the sine of the expression `expr`.

**Parameters:**

| Parameter | Type  | Description              |
| --------- | ----- | ------------------------ |
| expr      | float | Angle in **degrees**     |

**Returns:**

| Type  | Description              |
| ----- | ------------------------ |
| float | The sine of the angle    |

**Additional information:**

1. Input is in **degrees**, not radians.

**Example:**

```
fv1 = sin(30.0)
```

Computes the sine of 30 degrees (0.5) and stores it in `fv1`.

**See Also:** `cos`, `tan`, `asin`, `dtor`, `rtod`

### `sinh`

Returns the hyperbolic sine of the expression.

**Syntax:**

```
float sinh(float expr)
```

**Description:**

Return the hyperbolic sine of the expression `expr`.

**Parameters:**

| Parameter | Type  | Description    |
| --------- | ----- | -------------- |
| expr      | float | Input value    |

**Returns:**

| Type  | Description                    |
| ----- | ------------------------------ |
| float | The hyperbolic sine of expr    |

**Example:**

```
fv1 = sinh(2.0)
```

Computes the hyperbolic sine of 2.0 (approximately 3.6268) and stores it in `fv1`.

**See Also:** `cosh`, `tanh`, `asinh`, `dtor`, `rtod`

### `spatial_pulsing_end`

Stops spatial pulsing on a single channel.

**Syntax:**

```
spatial_pulsing_end(integer channel_number)
```

**Description:**

Disables spatial pulsing on the specified high-speed digital output channel. An internal sync is performed so the command is not executed during lookahead.

**Parameters:**

| Parameter      | Type    | Description                          |
| -------------- | ------- | ------------------------------------ |
| channel_number | integer | The channel to stop (numbered from 1) |

**Example:**

```
spatial_pulsing_end(1)
```

Stops spatial pulsing on channel 1.

**See Also:** `spatial_pulsing_start`, `spatial_pulsing_end_all`

### `spatial_pulsing_end_all`

Stops spatial pulsing on all channels.

**Syntax:**

```
spatial_pulsing_end_all()
```

**Description:**

Disables spatial pulsing on every high-speed digital output channel. An internal sync is performed so the command is not executed during lookahead.

**Example:**

```
spatial_pulsing_end_all()
```

Stops spatial pulsing on all channels.

**See Also:** `spatial_pulsing_start`, `spatial_pulsing_end`

### `spatial_pulsing_start`

Starts spatial pulsing on a high-speed digital output channel.

**Syntax:**

```
spatial_pulsing_start(integer channel_number, float distance, float duty_cycle)
```

**Description:**

Enables spatial pulsing on the specified high-speed digital output channel. The output is pulsed as a function of distance travelled rather than time: `distance` sets the spatial period of one pulse cycle and `duty_cycle` sets the percentage of that period for which the output is on. The channel must be configured in the database. An internal sync is performed so the command is not executed during lookahead.

**Parameters:**

| Parameter      | Type    | Description                                    |
| -------------- | ------- | ---------------------------------------------- |
| channel_number | integer | The high-speed digital output channel (numbered from 1) |
| distance       | float   | The spatial period of one pulse cycle. Must be greater than zero. |
| duty_cycle     | float   | The on-time as a percentage of the period, 0 to 100 |

**Example:**

```
spatial_pulsing_start(1, 5.0, 50.0)   { Pulse channel 1 every 5 mm at 50% }
```

Starts spatial pulsing on channel 1 with a 5 mm spatial period and a 50% duty cycle.

**See Also:** `spatial_pulsing_end`, `spatial_pulsing_end_all`

### `spinlimit`

Sets maximum spindle speed.

**Syntax:**

```
spinlimit value
spinlimit(x)y
spinlimit(x)(y)
```

**Description:**

Sets maximum spindle speed (in RPM) to prevent excessive speed when using constant surface speed (CSS) mode. As tool gets closer to workpiece center axis, this limit prevents dangerous speed increases.

**Parameters:**

| Parameter | Type    | Description                       |
| --------- | ------- | --------------------------------- |
| value     | float   | Maximum speed limit in RPM        |
| x         | integer | (Syntax 2) Spindle number (1-10)  |
| y         | float   | (Syntax 2) Speed limit            |

**Additional information:**

1. Not a standard word or block modifier - should be programmed in a block by itself.
2. This limit also applies to RPM mode and spindle overrides.

**Example:**

```
spinlimit 5000
spinlimit(2) 5000
```

Limits spindle 1 to a maximum of 5000 RPM, then limits spindle 2 to 5000 RPM.

**See Also:** `spinlimitss`, `spinlimitsss`, `spinlimitssss`

### `spinlimitss`

Sets maximum speed for spindle 2.

**Syntax:**

```
spinlimitss value
```

**Description:**

Sets maximum spindle 2 speed (in RPM). Same as `spinlimit` but specifically for spindle 2.

**Parameters:**

| Parameter | Type  | Description                 |
| --------- | ----- | --------------------------- |
| value     | float | Maximum speed limit in RPM  |

**Example:**

```
spinlimitss 5000
```

Limits spindle 2 to a maximum of 5000 RPM.

**See Also:** `spinlimit`, `spinlimitsss`, `spinlimitssss`

### `spinlimitsss`

Sets maximum speed for spindle 3.

**Syntax:**

```
spinlimitsss value
```

**Description:**

Sets maximum spindle 3 speed (in RPM). Same as `spinlimit` but specifically for spindle 3.

**Parameters:**

| Parameter | Type  | Description                 |
| --------- | ----- | --------------------------- |
| value     | float | Maximum speed limit in RPM  |

**Example:**

```
spinlimitsss 5000
```

Limits spindle 3 to a maximum of 5000 RPM.

**See Also:** `spinlimit`, `spinlimitss`, `spinlimitssss`

### `spinlimitssss`

Sets maximum speed for spindle 4.

**Syntax:**

```
spinlimitssss value
```

**Description:**

Sets maximum spindle 4 speed (in RPM). Same as `spinlimit` but specifically for spindle 4.

**Parameters:**

| Parameter | Type  | Description                 |
| --------- | ----- | --------------------------- |
| value     | float | Maximum speed limit in RPM  |

**Example:**

```
spinlimitssss 5000
```

Limits spindle 4 to a maximum of 5000 RPM.

**See Also:** `spinlimit`, `spinlimitss`, `spinlimitsss`

### `sprintf`

Returns a new, formatted string.

**Syntax:**

```
string sprintf(string format, args ...)
```

**Description:**

Returns a new, formatted string, where the format conversions are as described in the "Formatted Output" section.

**Parameters:**

| Parameter | Type   | Description                              |
| --------- | ------ | ---------------------------------------- |
| format    | string | Format string with conversion specifiers |
| args      | varies | Variable arguments for format specifiers |

**Returns:**

| Type   | Description            |
| ------ | ---------------------- |
| string | The formatted string   |

**Example:**

```
sv1 = sprintf("Value is %f", fv1)
sv2 = sprintf("X=%d, Y=%d", iv1, iv2)
```

Builds a formatted string containing the value of `fv1`, then a second string containing the integer values `iv1` and `iv2`.

**See Also:** `write`, `strdate`

### `sqrt`

Returns the square root of the expression.

**Syntax:**

```
float sqrt(float expr)
```

**Description:**

Return the square root of the expression `expr`.

**Parameters:**

| Parameter | Type  | Description            |
| --------- | ----- | ---------------------- |
| expr      | float | Value (must be ≥ 0)    |

**Returns:**

| Type  | Description               |
| ----- | ------------------------- |
| float | The square root of expr   |

**Additional information:**

1. The expression `expr` must be greater than or equal to 0.

**Example:**

```
fv1 = sqrt(5.0)
```

Computes the square root of 5.0 (approximately 2.2360) and stores it in `fv1`.

**See Also:** `pow`, `cbrt`

### `st`

Sets the spline type for spline interpolation.

**Syntax:**

```
st(type)
```

**Description:**

This may optionally be programmed in the `splineon` block, and sets the spline type to uniform, chord-length or B-spline, respectively. If no spline type is specified, the default type specified in the parameter `spl_method` is used instead.

*Uniform:*
Uniform splines should be used when interpolating rotational and linear axes where the rotational component forms a functional part of the path geometry. For these splines, care should be taken to ensure that the control points are approximately evenly spaced over the surface. That is, the displacements between control points should be in the ratio of 1:1.5 to each other at most. Otherwise, there may be severe path overshoots.

*Chord-Length:*
Chord-length splines should be used when interpolating linear axes only. For these splines, the control point spacing is not critical and can be highly uneven. (Uniform splines can also be used when interpolating linear axes only, but they are more restrictive because of the need for even spacing of the control points.)

*B-spline:*
B-splines can be used when interpolating both linear and rotational axes. For these splines, the control point spacing is not critical, although duplicate control points are not permitted. B-splines are generally smoother than the other two types and have curvature continuity (i.e. B-splines are `G2` continuous). Note that B-splines will pass through the start and end points, but generally will not pass through the intermediate control points. Tension factor and dummy points do not apply to B-splines, and will simply be ignored.

**Parameters:**

| Parameter | Type   | Description                                                                    |
| --------- | ------ | ------------------------------------------------------------------------------ |
| type      | string | The spline type. Can be `uniform`, `chord`, or `bspline`.                      |

**Additional information:**

1. Programming of the spline type is modal and will remain in effect until reprogrammed, or the CNC is powered off.
2. Programming of the spline type is optional.

**Example:**

```
splineon st(chord)
```

Switches on spline mode and sets the spline type to chord-length.

**See Also:** `splineon`, `splineoff`, `tf`

### `strdate`

Returns the current date and time as a string.

**Syntax:**

```
string strdate(string format)
```

**Description:**

Returns the current date and time as a string. The format string, if supplied, is that supported by the C Run-Time library function `strftime`. If format is omitted, returns a string formatted according to the system parameter `*date_format` (Default is typically "%c").

**Parameters:**

| Parameter | Type   | Description                              |
| --------- | ------ | ---------------------------------------- |
| format    | string | Optional format string (strftime compatible) |

**Returns:**

| Type   | Description                        |
| ------ | ---------------------------------- |
| string | The formatted date/time string     |

**Example:**

```
timestamp = strdate("%Y/%m/%d %H:%M:%S")
```

Returns the current date and time formatted as year/month/day hours:minutes:seconds (for example "2013/12/10 09:34:56").

**See Also:** `sprintf`

### `strext`

Extracts a substring from a string.

**Syntax:**

```
string strext(string old_string, integer index, integer len)
```

**Description:**

Extracts the sub-string of length `len` starting at position `index`.

**Parameters:**

| Parameter  | Type    | Description                |
| ---------- | ------- | -------------------------- |
| old_string | string  | Source string              |
| index      | integer | Starting position          |
| len        | integer | Length to extract          |

**Returns:**

| Type   | Description               |
| ------ | ------------------------- |
| string | The extracted substring   |

**Example:**

```
new_str = strext("ANCAMotion", 4, 3)
```

Extracts three characters starting at position 4 of "ANCAMotion", giving "Mot".

**See Also:** `strlen`, `strins`, `strrpl`

### `strins`

Inserts a string into another string at a specified position.

**Syntax:**

```
string strins(string src_str, string ins_str, integer index)
```

**Description:**

Inserts `ins_str` into `src_str` at position `index`.

**Parameters:**

| Parameter | Type    | Description            |
| --------- | ------- | ---------------------- |
| src_str   | string  | Source string          |
| ins_str   | string  | String to insert       |
| index     | integer | Insertion position     |

**Returns:**

| Type   | Description                              |
| ------ | ---------------------------------------- |
| string | The new string with ins_str inserted    |

**Example:**

```
src_str = "ANCA MON"
sv0 = strins(src_str, "TIO", 7)
```

Inserts the string "TIO" into "ANCA MON" at position `7`, resulting in "ANCA MOTION" and stores it in `sv0`
**See Also:** `strext`, `strrpl`, `strlen`

### `strlen`

Returns the length of a string.

**Syntax:**

```
integer strlen(string src_str)
```

**Description:**

Returns the length of the string `src_str`.

**Parameters:**

| Parameter | Type   | Description     |
| --------- | ------ | --------------- |
| src_str   | string | Source string   |

**Returns:**

| Type    | Description              |
| ------- | ------------------------ |
| integer | The length of the string |

**Example:**

```
length = strlen(src_str)
```

Stores the number of characters in `src_str` in the variable `length`.

**See Also:** `strext`, `strins`

### `strrpl`

Replaces characters in a string at a specified position.

**Syntax:**

```
string strrpl(string src_str, string rpl_str, integer index)
```

**Description:**

Inserts `rpl_str` into `src_str` at position `index`, **overwriting** any previous contents.

**Parameters:**

| Parameter | Type    | Description            |
| --------- | ------- | ---------------------- |
| src_str   | string  | Source string          |
| rpl_str   | string  | Replacement string     |
| index     | integer | Starting position      |

**Returns:**

| Type   | Description                                    |
| ------ | ---------------------------------------------- |
| string | The new string with characters overwritten    |

**Additional information:**

1. Overwrites existing characters rather than inserting.

**Example:**

```
new_str = strrpl("ANCAMotion", "Movement", 4)
```

Overwrites the characters of "ANCAMotion" from position 4 with "Movement", giving "ANCAMovement".

**See Also:** `strins`, `strext`

### `strtoch`

Returns the character code of the first character in a string.

**Syntax:**

```
integer strtoch(string arg_str)
```

**Description:**

Returns the character code (as an unsigned 1 byte integer) of the first character in string `arg_str`.

**Parameters:**

| Parameter | Type   | Description     |
| --------- | ------ | --------------- |
| arg_str   | string | Input string    |

**Returns:**

| Type    | Description                       |
| ------- | --------------------------------- |
| integer | ASCII value of first character    |

**Additional information:**

1. Returns ASCII value of first character only.

**Example:**

```
chnum = strtoch("ABCD")
```

Returns the character code of the first character of "ABCD" (65, the ASCII code for 'A').

**See Also:** `chtostr`

### `sync`

Synchronizes all lookahead with the machine.

**Syntax:**

```
sync
```

**Description:**

Synchronizes all lookahead with the machine. Forces the program to wait until the machine has executed all moves prior to the sync.

**Actions when executed:**

1. Terminates all Path compensation lookahead
2. Terminates all Velocity lookahead
3. Waits for machine to catch up
4. Latches last command position back into dimension word variables (`X`, `Y`, `Z`, etc.)
5. Program lookahead continues after machine reaches target point

**Additional information:**

1. Sync commands slow down program execution.
2. Will cause Velocity and Path compensation lookahead to break (may produce undesired path).
3. Terminates the retrace queue - operator cannot retrace over a sync command.

**Example:**

```
rapid X(pallet_posn_x) Y(pallet_posn_y)
sync { Break all lookahead }
if ((plc)bv180 = on) then
  calls "load_from_pallet"
else
  write("pallet not ready\n")
ifend
```

Performs a rapid move, breaks all lookahead with `sync` so the machine reaches the target before the test, then loads from the pallet or reports that it is not ready depending on the PLC boolean.

**See Also:** `waitplc`

### `system`

Executes an operating system call.

**Syntax:**

```
system expr
```

**Description:**

Executes an operating system call from a part program. Allows programmers to access operating system functions built into the 3DX-NT CNC.

**Parameters:**

| Parameter | Type   | Description                                |
| --------- | ------ | ------------------------------------------ |
| expr      | string | Command string passed to the operating system |

**Returns:**

| Type    | Description                              |
| ------- | ---------------------------------------- |
| integer | Value returned by the operating system function |

**Additional information:**

1. May **not** be used to run programs requiring standard screen I/O.
2. Format of expr should be exactly as typed from shell.
3. Normally use "&" to place task in background (prevents blocking).
4. **Take CARE when using this function.**

**Example:**

```
system "mkdir 3:/tg7/pp/tmp"
system "my_appl &"
```

Creates a new directory, then launches an application in the background using the trailing `&`.

**See Also:** `fexists`, `fdelete`

### `T`

Selects a tool for tool change.

**Syntax:**

```
T integer
T(expression)
```

**Description:**

Selects a particular tool in preparation for a tool change. Each tool is referred to by a number. Once selected, the new tool is held ready to be swapped with the current tool.

**Parameters:**

| Parameter  | Type       | Description                     |
| ---------- | ---------- | ------------------------------- |
| integer    | integer    | Direct tool number              |
| expression | expression | Indirect specification          |

**Additional information:**

1. May be programmed ahead of when needed, allowing tool changer to position while machining.
2. Tool number and tool offset group number need not be the same.
3. The actual swapping is executed by `toolchange` (`M6`).

**Example:**

```
T 12
T(iv4)
toolselect 23
```

Selects tool 12 directly, selects a tool from variable `iv4`, and gets tool 23 ready in the swapper with `toolselect`.

**See Also:** `toolselect`, `tooloffset`, `wheelselect`

### `tan`

Returns the tangent of the expression.

**Syntax:**

```
float tan(float expr)
```

**Description:**

Return the tangent of the expression `expr`.

**Parameters:**

| Parameter | Type  | Description              |
| --------- | ----- | ------------------------ |
| expr      | float | Angle in **degrees**     |

**Returns:**

| Type  | Description                |
| ----- | -------------------------- |
| float | The tangent of the angle   |

**Additional information:**

1. Input is in **degrees**, not radians.

**Example:**

```
fv1 = tan(45.0)
```

Computes the tangent of 45 degrees (1.0) and stores it in `fv1`.

**See Also:** `sin`, `cos`, `atan`, `dtor`, `rtod`

### `tanh`

Returns the hyperbolic tangent of the expression.

**Syntax:**

```
float tanh(float expr)
```

**Description:**

Return the hyperbolic tangent of the expression `expr`.

**Parameters:**

| Parameter | Type  | Description    |
| --------- | ----- | -------------- |
| expr      | float | Input value    |

**Returns:**

| Type  | Description                       |
| ----- | --------------------------------- |
| float | The hyperbolic tangent of expr    |

**Example:**

```
fv1 = tanh(2.0)
```

Computes the hyperbolic tangent of 2.0 (approximately 0.9640) and stores it in `fv1`.

**See Also:** `sinh`, `cosh`, `atanh`

### `tf`

Tension factor represents the tautness of a spline.

**Syntax:**

```
tf tightness
tf(expression)
```

**Description:**

The tension factor represents the tautness of a spline. This refers to how tightly the spline will "wrap" itself around the given control points. Tension factor applies to uniform and chord-length splines only; it has no effect on B-splines. The tension factor may optionally be programmed in the `splineon` block and/or in any control point block (with the dimension words). When programming a spline, the tension factor is optional. If no tension factor is specified, the default value specified in the parameter `spl_tension` is used instead. It is recommended that a tension factor of `0` is used for most splines. The tension factor can be altered partway through a spline, by programming the new tension factor in any of the control point blocks of the spline.

**Parameters:**

| Parameter  | Type       | Description                                                                                                   |
| ---------- | ---------- | ------------------------------------------------------------------------------------------------------------- |
| tightness  | float      | `A` value between 0.0 and 1.0, with 0 representing the loosest a spline will get, and 1 representing the tightest. |
| expression | expression | An expression evaluating to a tension factor value between 0.0 and 1.0.                                          |

**Example:**

```
splineon tf1.0 { Set the Tension Factor to the TAUTEST it can get }
```

Switches on spline mode and sets the tension factor to 1.0, the tautest setting.

**See Also:** `splineon`, `splineoff`

### `tg_cam`

Executes the specified cam profile.

**Syntax:**

```
tg_cam(integer cam_id)
```

**Description:**

Execute the specified cam. The cam profile is checked against the machine's individual Joint parameters (j.max_velocity, j.max_accel and j.max_jerk) when `tg_cam()` is called. If any of these limits are exceeded, a ppi execution error is raised and the cam is not run.

**Parameters:**

| Parameter | Type    | Description                              |
| --------- | ------- | ---------------------------------------- |
| cam_id    | integer | The ID of the cam to execute             |

**Additional information:**

1. Cam points are programmed in User Frame.
2. Rows in the cam correspond to machine positions at intervals of consecutive Machine Update Periods (typically 4ms).
3. The machine must be stationary before invoking the cam.
4. No feedrate override is available during cam execution.
5. Feedhold and ABORT will stop a cam immediately.

**Example:**

```
cam_id = tg_cam_alloc(3)
tg_cam_write(cam_id, 0.0, 0.0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
tg_cam_write(cam_id, 1.0, 0.5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1)
tg_cam_write(cam_id, 2.0, 0.0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2)
tg_cam(cam_id)
tg_cam_free(cam_id)
```

Allocates a three-row cam, writes `X` and `Y` positions for each Machine Update Period, executes the cam, then frees it.

**See Also:** `tg_cam_alloc`, `tg_cam_write`, `tg_cam_read`, `tg_cam_reverse`, `tg_cam_rows`, `tg_cam_free`, `tg_cam_free_all`

### `tg_cam_alloc`

Allocates rows for a cam profile and returns the cam ID.

**Syntax:**

```
integer tg_cam_alloc(integer rows)
```

**Description:**

Allocate the number of rows in the cam profile and return the id of the cam.

**Parameters:**

| Parameter | Type    | Description                              |
| --------- | ------- | ---------------------------------------- |
| rows      | integer | The number of rows to allocate           |

**Returns:**

| Type    | Description                              |
| ------- | ---------------------------------------- |
| integer | The ID of the allocated cam              |

**Additional information:**

1. Current memory limit is 200,000 rows, giving a profiling time (ms) of (200,000) x (machine update period).

**Example:**

```
cam_id = tg_cam_alloc(100)
```

Allocates a cam profile with 100 rows and stores the returned cam ID.

**See Also:** `tg_cam`, `tg_cam_write`, `tg_cam_free`, `tg_cam_free_all`

### `tg_cam_free`

Frees the memory allocated to a specified cam.

**Syntax:**

```
tg_cam_free(integer cam_id)
```

**Description:**

Free the memory allocated to the specified cam.

**Parameters:**

| Parameter | Type    | Description                              |
| --------- | ------- | ---------------------------------------- |
| cam_id    | integer | The ID of the cam to free                |

**Example:**

```
tg_cam_free(cam_id)
```

Frees the memory allocated to the cam identified by `cam_id`.

**See Also:** `tg_cam_alloc`, `tg_cam_free_all`

### `tg_cam_free_all`

Frees all allocated cams.

**Syntax:**

```
tg_cam_free_all()
```

**Description:**

Free all the Cams.

**Example:**

```
tg_cam_free_all()
```

Frees the memory allocated to every cam.

**See Also:** `tg_cam_free`, `tg_cam_alloc`

### `tg_cam_read`

Reads axis positions from a specified cam at a specified row.

**Syntax:**

```
tg_cam_read(integer cam_id, float &X, float &Y, float &Z, float &V, float &A, float &B, float &C, float &U, float &P, float &W, float &AP, integer row)
```

**Description:**

Read the axis positions from the specified cam and row.

**Parameters:**

| Parameter | Type    | Description                              |
| --------- | ------- | ---------------------------------------- |
| cam_id    | integer | The ID of the cam                        |
| &X...&AP  | float   | Variables to receive axis positions      |
| row       | integer | The row number to read from              |

**Example:**

```
tg_cam_read(cam_id, &fv0, &fv1, &fv2, &fv3, &fv4, &fv5, &fv6, &fv7, &fv8, &fv9, &fv10, 5)
```

Reads the axis positions stored at row 5 of the cam into the corresponding variables.

**See Also:** `tg_cam_write`, `tg_cam_alloc`, `tg_cam`

### `tg_cam_reverse`

Executes a cam in reverse direction (last row to first row).

**Syntax:**

```
tg_cam_reverse(integer cam_id)
```

**Description:**

Execute the specified cam in the reverse direction (last row to first row).

**Parameters:**

| Parameter | Type    | Description                              |
| --------- | ------- | ---------------------------------------- |
| cam_id    | integer | The ID of the cam to execute in reverse  |

**Example:**

```
tg_cam_reverse(cam_id)
```

Executes the cam identified by `cam_id` from its last row to its first.

**See Also:** `tg_cam`, `tg_cam_alloc`, `tg_cam_write`

### `tg_cam_rows`

Returns the number of rows in a specified cam.

**Syntax:**

```
integer tg_cam_rows(integer cam_id)
```

**Description:**

Return the number of rows in the specified cam.

**Parameters:**

| Parameter | Type    | Description                              |
| --------- | ------- | ---------------------------------------- |
| cam_id    | integer | The ID of the cam                        |

**Returns:**

| Type    | Description                              |
| ------- | ---------------------------------------- |
| integer | The number of rows in the cam            |

**Example:**

```
numRows = tg_cam_rows(cam_id)
```

Stores the number of rows in the cam identified by `cam_id` in `numRows`.

**See Also:** `tg_cam_alloc`, `tg_cam_read`, `tg_cam_write`

### `tg_cam_write`

Writes axis positions to a specified cam profile at a specified row.

**Syntax:**

```
tg_cam_write(integer cam_id, float X, float Y, float Z, float V, float A, float B, float C, float U, float P, float W, float AP, integer row)
```

**Description:**

Write axis positions to the specified cam profile at the specified row.

**Parameters:**

| Parameter | Type    | Description                              |
| --------- | ------- | ---------------------------------------- |
| cam_id    | integer | The ID of the cam                        |
| X...AP    | float   | Axis positions to write                  |
| row       | integer | The row number to write to               |

**Example:**

```
tg_cam_write(cam_id, 1.0, 0.5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1)
```

Writes the `X` and `Y` positions (all other axes zero) into row 1 of the cam.

**See Also:** `tg_cam_read`, `tg_cam_alloc`, `tg_cam`

### `tg_prof_alloc`

Allocates memory for a Profile Device and returns a device handle.

**Syntax:**

```
integer tg_prof_alloc(rows, columns)
```

**Description:**

Create and allocate a profile device. Profile devices are a form of 2D arrays for EPPL programs that can be allocated and referenced dynamically.

**Parameters:**

| Parameter | Type    | Description                                               |
| --------- | ------- | --------------------------------------------------------- |
| rows      | integer | The number of rows to allocate for the profile device     |
| columns   | integer | (Optional) The number of columns to allocate              |

**Returns:**

| Type    | Description                                    |
| ------- | ---------------------------------------------- |
| integer | An ID representing the new profile device      |

**Example:**

```
profile_device_id = tg_prof_alloc(100)
profile_device_id_2 = tg_prof_alloc(100, 9)
```

Allocates a 100-row profile device, then a second profile device with 100 rows and 9 columns, storing each device ID.

**See Also:** `tg_prof_write`, `tg_prof_read`, `tg_prof_free_all`

### `tg_prof_alloc_protected`

Allocates a protected profile device and returns its handle.

**Syntax:**

```
integer tg_prof_alloc_protected(rows, columns)
```

**Description:**

Allocates a profile device in the same way as `tg_prof_alloc`, but marks it as protected. Unlike a normal profile device, a protected profile device is not deallocated automatically, so its data persists. If `columns` is omitted a default number of 5 columns is used.

**Parameters:**

| Parameter | Type    | Description                                             |
| --------- | ------- | ------------------------------------------------------- |
| rows      | integer | The number of rows to allocate                          |
| columns   | integer | (Optional) The number of columns. Defaults to 5 if omitted. |

**Returns:**

| Type    | Description                                      |
| ------- | ------------------------------------------------ |
| integer | The ID of the allocated protected profile device |

**Example:**

```
profile_device_id = tg_prof_alloc_protected(100)
profile_device_id_2 = tg_prof_alloc_protected(100, 9)
```

Allocates a 100-row protected profile device (with default 5 columns), then a second protected profile device with 100 rows and 9 columns.

**See Also:** `tg_prof_alloc`, `tg_prof_free_all_protected`, `tg_prof_write`

### `tg_prof_col_count`

Returns the number of columns in a Profile Device.

**Syntax:**

```
integer tg_prof_col_count(profileDeviceID)
```

**Description:**

Return the number of columns in a Profile Device.

**Parameters:**

| Parameter       | Type    | Description              |
| --------------- | ------- | ------------------------ |
| profileDeviceID | integer | The profile device ID    |

**Returns:**

| Type    | Description                                       |
| ------- | ------------------------------------------------- |
| integer | The number of columns in the profile device       |

**Example:**

```
numColumns = 0
numColumns = tg_prof_col_count(profileDevice)
```

Reads the number of columns in the profile device `profileDevice` into `numColumns`.

**See Also:** `tg_prof_row_count`, `tg_prof_alloc`

### `tg_prof_cpy`

Copies the contents of one profile device to another.

**Syntax:**

```
tg_prof_cpy(integer target_id, integer source_id)
```

**Description:**

Copies all data from the source profile device to the target profile device. If the source and target IDs are the same, the function does nothing. Both profile devices must already be allocated and have matching sizes.

**Parameters:**

| Parameter | Type    | Description                              |
| --------- | ------- | ---------------------------------------- |
| target_id | integer | The ID of the profile device to copy into |
| source_id | integer | The ID of the profile device to copy from |

**Example:**

```
tg_prof_cpy(profile_device_id_2, profile_device_id_1)
```

Copies the contents of profile device 1 into profile device 2.

**See Also:** `tg_prof_alloc`, `tg_prof_read`, `tg_prof_write`

### `tg_prof_free`

Deletes a profile device and its associated data.

**Syntax:**

```
tg_prof_free(profileDeviceID)
```

**Description:**

Delete a profile device and its associated data.

**Parameters:**

| Parameter       | Type    | Description           |
| --------------- | ------- | --------------------- |
| profileDeviceID | integer | The profile device ID |

**Returns:**

Nothing.

**Example:**

```
tg_prof_free(profileDeviceID)
```

Deletes the profile device identified by `profileDeviceID` and releases its memory.

**See Also:** `tg_prof_alloc`, `tg_prof_free_all`

### `tg_prof_free_all`

Deletes all profile devices and their associated data.

**Syntax:**

```
tg_prof_free_all()
```

**Description:**

Delete all profile devices and their associated data.

**Example:**

```
tg_prof_free_all()
```

Deletes every allocated profile device and releases all associated memory.

**See Also:** `tg_prof_alloc`, `tg_prof_free_all_protected`

### `tg_prof_free_all_protected`

Frees all protected profile devices.

**Syntax:**

```
tg_prof_free_all_protected()
```

**Description:**

Deletes every protected profile device (those allocated with `tg_prof_alloc_protected`) and releases their memory. Normal profile devices are not affected.

**Example:**

```
tg_prof_free_all_protected()
```

Frees every protected profile device and releases its memory.

**See Also:** `tg_prof_alloc_protected`, `tg_prof_free_all`, `tg_prof_free`

### `tg_prof_read`

Reads data from a row in a Profile Device.

**Syntax:**

```
tg_prof_read(profileDeviceID, &var1, &var2, ..., &varN, rowIndex)
```

**Description:**

Read data from a row in a profile device.

**Parameters:**

| Parameter       | Type    | Description                                                         |
| --------------- | ------- | ------------------------------------------------------------------- |
| profileDeviceID | integer | The profile ID of the Profile Device (as returned by `tg_prof_alloc`) |
| var1, ..., varN | float   | Floating point variables to store the data read                     |
| rowIndex        | integer | The row of the Profile Device to read from                          |

**Additional information:**

1. Variables must be passed by reference using the `&` operator.

**Example:**

```
tg_prof_read(profileDeviceID, &var1, &var2, &var3, 4)
```

Reads the three column values from row 4 of the profile device into `var1`, `var2` and `var3`.

**See Also:** `tg_prof_write`, `tg_prof_alloc`

### `tg_prof_row_count`

Returns the number of rows in a Profile Device.

**Syntax:**

```
integer tg_prof_row_count(profileDeviceID)
```

**Description:**

Return the number of rows in a Profile Device.

**Parameters:**

| Parameter       | Type    | Description              |
| --------------- | ------- | ------------------------ |
| profileDeviceID | integer | The profile device ID    |

**Returns:**

| Type    | Description                                    |
| ------- | ---------------------------------------------- |
| integer | The number of rows in the profile device       |

**Example:**

```
numRows = 0
numRows = tg_prof_row_count(profileDevice)
```

Reads the number of rows in the profile device `profileDevice` into `numRows`.

**See Also:** `tg_prof_col_count`, `tg_prof_alloc`

### `tg_prof_share_name`

Returns the global shared-memory share name of a profile device.

**Syntax:**

```
string tg_prof_share_name(profile_device_id)
```

**Description:**

Return the global shared-memory share name associated with the specified profile device. The profile device identifier is one-based.

**Parameters:**

| Parameter         | Type    | Description                                                            |
| ----------------- | ------- | ---------------------------------------------------------------------- |
| profile_device_id | integer | The profile ID of the profile device (as returned by `tg_prof_alloc`). |

**Returns:**

| Type   | Description                                            |
| ------ | ------------------------------------------------------ |
| string | The global share name of the specified profile device. |

**Example:**

```
share_name = ""
share_name = tg_prof_share_name(profile_device)
```

Retrieves the global shared-memory share name of the profile device identified by `profile_device` into the string variable `share_name`.

**See Also:** `tg_prof_read`, `tg_prof_write`, `tg_prof_row_count`, `tg_prof_col_count`

### `tg_prof_write`

Writes data to a row in a Profile Device.

**Syntax:**

```
tg_prof_write(profileDeviceID, val1, val2, ..., valN, rowIndex)
```

**Description:**

Write data to a row in a profile device.

**Parameters:**

| Parameter       | Type    | Description                                                         |
| --------------- | ------- | ------------------------------------------------------------------- |
| profileDeviceID | integer | The profile ID of the Profile Device (as returned by `tg_prof_alloc`) |
| val1, ..., valN | float   | A series of floating point values to write into the row             |
| rowIndex        | integer | The row of the Profile Device to write to                           |

**Example:**

```
tg_prof_write(profileDeviceID, 1.0, 5.6, 9.7, 4)
```

Writes the values 1.0, 5.6 and 9.7 into row 4 of the profile device.

**See Also:** `tg_prof_read`, `tg_prof_alloc`

### `tg_runout_comp`

Enables tool grinder runout compensation.

**Syntax:**

```
tg_runout_comp(float X1, float theta1, float offset1, float X2, float theta2, float offset2)
```

**Description:**

Enables tool grinder runout compensation. Runout compensation is typically used to compensate for a slightly off-centre tool. Using this function, the compensation value can change based on the position of joint number 1 (X).

**theta** and **offset** give the position of the centreline of the tool in respect to the centreline of the spindle (i.e. `A` axis). **offset** determines the distance between the centreline of the tool and the centreline of the spindle. **theta** shows the angle between the positive direction of the `Z` axis and the line connecting the centreline of the `A` axis to the centreline of the tool when `A`=0.

Activating tool grinder runout compensation will not initially move `Y` and `Z`. Instead the displayed position will change to reflect the compensation. When the compensation is active, if A or X move, `Y` and `Z` will move as well to compensate for the runout.

In order to have a fixed compensation applied (**offset1** and **theta1**) regardless of the value of x, `tg_runout_comp(0, theta1, offset1, 0, theta1, offset1)` can be used.

**Parameters:**

| Parameter | Type  | Description                                          |
| --------- | ----- | ---------------------------------------------------- |
| x1        | float | The x value at which **offset1** and **theta1** are measured |
| theta1    | float | The angle (in degrees) between the positive direction of the `Z` axis and the line connecting the centreline of the spindle (i.e. the `A` axis) to the centreline of the tool at x = **x1** |
| offset1   | float | The distance between the centreline of the spindle (i.e. the `A` axis) and the centreline of the tool at x = **x1** |
| x2        | float | The x value at which **offset2** and **theta2** are measured |
| theta2    | float | The angle (in degrees) between the positive direction of the `Z` axis and the line connecting the centreline of the spindle (i.e. the `A` axis) to the centreline of the tool at x = **x2** |
| offset2   | float | The distance between the centreline of the spindle (i.e. the `A` axis) and the centreline of the tool at x = **x2** |

**Example:**

```
tg_runout_comp(-100.0, 0.0, 0.01, -150.0, 0.0, 0.02)
```

After executing this, offset will change from 0.01mm to 0.02mm when x goes from -100mm to -150mm.

**See Also:** `tg_runout_comp_cancel`, `runout_comp`

### `tg_runout_comp_cancel`

Cancels tool grinder runout compensation.

**Syntax:**

```
tg_runout_comp_cancel()
```

**Description:**

Cancels tool grinder runout compensation.

**Example:**

```
tg_runout_comp_cancel()
```

Cancels the tool grinder runout compensation previously activated by `tg_runout_comp`.

**See Also:** `tg_runout_comp`

### `tooloffset`

Selects a tool offset group.

**Syntax:**

```
tooloffset group_number
tooloffset(expression)
```

**Description:**

Selects a particular tool offset group from the tool table. Same as the D command.

**Parameters:**

| Parameter    | Type       | Description                        |
| ------------ | ---------- | ---------------------------------- |
| group_number | integer    | Tool offset group number           |
| expression   | expression | Expression evaluating to group number |

**Example:**

```
tooloffset 6        { selects tool offset group 6 }
tooloffset(fv3)     { selects group referred to by fv3 }
```

Selects tool offset group 6, then selects the group referenced by `fv3`.

**See Also:** `D`, `toolselect`, `eff`

### `toolselect`

Selects a tool for tool change.

**Syntax:**

```
toolselect integer
toolselect(expression)
```

**Description:**

Selects a particular tool in preparation for a tool change. Same as the T command.

**Parameters:**

| Parameter  | Type       | Description                     |
| ---------- | ---------- | ------------------------------- |
| integer    | integer    | Direct tool number              |
| expression | expression | Indirect specification          |

**Example:**

```
toolselect 12       { Select tool number 12 }
toolselect 23       { Get tool 23 ready in swapper }
X34.87 Y22.98       { Continue machining with old tool }
toolchange tooloffset 23  { Change tool and load offsets }
```

Selects tool 12, then gets tool 23 ready in the swapper while machining continues with the current tool, and finally changes to tool 23 and loads its offsets.

**See Also:** `T`, `tooloffset`, `wheelselect`

### `trunc`

Truncates a float expression to an integer.

**Syntax:**

```
integer trunc(float expr)
```

**Description:**

Convert the float expression `expr` to an integer by truncating the fractional part.

**Parameters:**

| Parameter | Type  | Description          |
| --------- | ----- | -------------------- |
| expr      | float | Float value to truncate |

**Returns:**

| Type    | Description                 |
| ------- | --------------------------- |
| integer | The truncated integer value |

**Additional information:**

1. Returns integer type.
2. Float values > `maxint` return `maxint`; values < -`maxint` return -`maxint`.

**Example:**

```
iv1 = trunc(1.01)
iv2 = trunc(1.99)
iv3 = trunc(-1.01)
iv4 = trunc(-1.99)
```

Truncates each value towards zero to an integer: 1.01 and 1.99 both give 1, while -1.01 and -1.99 both give -1.

**See Also:** `round`, `mod`

### `unitcv`

Converts millimetres to inches if in `inch` mode.

**Syntax:**

```
float unitcv(float mm_expr)
```

**Description:**

Convert the units of the expression `mm_expr` from millimetres to inches if `inch` mode (`G70`) is currently modal. If `metric` mode (`G71`) is currently modal, this function will return `mm_expr` unchanged.

**Parameters:**

| Parameter | Type  | Description             |
| --------- | ----- | ----------------------- |
| mm_expr   | float | Value in millimetres    |

**Returns:**

| Type  | Description                                              |
| ----- | -------------------------------------------------------- |
| float | The value in current units (converted if in `inch` mode)   |

**Additional information:**

1. Used for writing subprograms that work independent of current dimension mode.
2. System variables like `g_posn_uf[]` and `g_probed_uf[]` are always stored in mm—use `unitcv()` when accessing these.

**Example:**

```
F(unitcv(500.0))
G1 X(unitcv(g_probed_uf[2]) + 2.0)
```

Sets the feedrate to 500 mm/min regardless of the current units mode, then commands a linear move whose X target is derived from a stored user-frame position converted to the mm.

**See Also:** `posnlatch`, `probelatch`

### `waitplc`

Waits for PLC scans to complete.

**Syntax:**

```
waitplc
waitplc(expr)
```

**Description:**

Waits for the specified number of PLC scans to complete. Ensures PLC has processed changes before EPPL program continues.

**Parameters:**

| Parameter | Type    | Description                                    |
| --------- | ------- | ---------------------------------------------- |
| expr      | integer | (Optional) Number of PLC scans. Defaults to 1. |

**Additional information:**

1. Program a `sync` command before using this to ensure not executed in look-ahead.
2. No bounds checking on expr - be careful with the value.
3. Facility dependent on appropriate PLC coding.

**Example:**

```
waitplc(5)              { Wait for 5 PLC scans }

(plc)bv304 = on         { Tell PLC to perform action }
sync
waitplc                 { Guarantee PLC has recognised bit change }
G1 X100 stopifnot (plc)bv304
```

Waits for five PLC scans, then sets a PLC bit, synchronises, waits one scan to guarantee the PLC has recognised the change, and continues the move conditioned on that bit.

**See Also:** `sync`

### `wclose`

Closes a window.

**Syntax:**

```
wclose
```

**Description:**

Closes a window that was opened by `wopen` or implicitly by `vdu`/`keyboard` stream usage.

**Additional information:**

1. Window closed automatically on: rewind, deactivate, cancel lookahead, program abort, active program editing, conditional move firing.

**Example:**

```
wopen
write("Job complete\n")
wclose
```

Opens a window, writes a message to it, then closes the window with `wclose`.

**See Also:** `wopen`

### `wopen`

Opens a window for `vdu` output.

**Syntax:**

```
wopen
```

**Description:**

Opens a window for `vdu` output or `keyboard` input. Window opening is implicit when `write()` with `vdu` stream or `read()`/`readkey()` with `keyboard` stream is called.

**Additional information:**

1. Usually not necessary to explicitly program `wopen` unless opening window prior to use or needing the window handle.

**Example:**

```
wopen
write("Ready\n")
```

Explicitly opens a window before writing a message to the `vdu`.

**See Also:** `wclose`, `write`

### `write`

Outputs text to `vdu`, `printer`, or file.

**Syntax:**

```
write(format_string, ...)
write(stream, format_string, ...)
```

**Description:**

Outputs text to `vdu`, `printer`, or disk file using format specifications.

**Parameters:**

| Parameter     | Type   | Description                                     |
| ------------- | ------ | ----------------------------------------------- |
| stream        | stream | (Optional) Stream identifier `vdu`, `printer`, or disk (defaults to `vdu`)  |
| format_string | string | String with format specifiers                   |
| ...           | varies | Values to format                                |

**Format Characters:**

| Format | Description            |
| ------ | ---------------------- |
| %b     | Boolean `on`/`off`         |
| %B     | Boolean `true`/`false`     |
| %u     | Unsigned integer       |
| %d, %i | Decimal integer        |
| %x, %X | Hexadecimal            |
| %c     | Character              |
| %s     | String                 |
| %f     | Float                  |

**Escape Sequences:**

| Escape | Description      |
| ------ | ---------------- |
| \n     | Newline          |
| \t     | Tab              |
| \l     | Clear to EOL     |
| \s     | Clear to EOS     |

**Example:**

```
write("Variable IV1 = %d\n", iv1)
```

Writes the value of integer variable `iv1` to the `vdu`, followed by a newline.

**See Also:** `read`, `sprintf`, `open`

### `zgc`

Obsolete Command.

**Description:**

Under the CiA402 standard, the servo-drive controls the homing sequence and the change of reference frame, so this command is no longer required.

### `zrc`

Zero Rotation Count.

**Syntax:**

```
zrc [jnt]
```

**Description:**

Used to "unwind" a continuously rotating joint, leaving the base rotation within a +180 to -180 degree range. It performs a similar function to `G49`, but in joint frame. It is intended primarily for homing type actions on spindles with absolute encoders, but can be used elsewhere as required.

**Parameters:**

| Parameter | Type    | Description                                                        |
| --------- | ------- | ------------------------------------------------------------------ |
| jnt       | integer | Joint number. Valid only for rotary joints without soft limits.    |

**Error Codes:**

| Return Code | PPI Execution Error                          |
| ----------- | -------------------------------------------- |
| 0           | Success                                      |
| 1           | `zrc` Invalid - Joint is not rotary            |
| 2           | `zrc` Disallowed - Joint has Soft Limits       |
| 3           | `zrc` Not supported by Joint                   |
| other       | `zrc` Failed - Error code=<e>                  |

**Additional information:**

1. If you have removed a large cumulative rotation using `G49`, this will be evident as a large difference between Joint and Machine positions. If you then cancel joint turns with `zrc`, this difference will be reflected back into the machine frame. Issue another `G49` if needed.
2. `zrc` is **passive** - NO motion is generated. The change is in frame positions only.

**Example:**

```
f_save = F
F(100000)
zrc 4
joint 4, 0.0
G49 A0
F(f_save)
```

Saves the current feedrate, sets a high feedrate, unwinds joint 4 with `zrc`, moves joint 4 to zero, cancels any remaining offset with `G49`, and restores the original feedrate.

**See Also:** `zgc`, `clearlo`, `clearsa`, `G49`
