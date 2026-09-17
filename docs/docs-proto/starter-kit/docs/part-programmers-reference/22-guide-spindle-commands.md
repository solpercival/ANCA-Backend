# Spindle Commands

The spindle commands start, stop, orient and set the speed of the machine's spindles. The CNC caters for four spindles operating concurrently out of the box, and for up to ten spindles with additional setup; the number available on a particular machine depends on the PLC. Spindles may be controlled by separate spindle controllers or allocated to one of the programmable axes (a joint). Commands for spindles 2, 3 and 4 mirror those for spindle 1, distinguished by the suffix codes `ss` (spindle 2), `sss` (spindle 3) and `ssss` (spindle 4).

**Commands and Variables**

| Name                                                    | Type     | Description                                                               |
| ------------------------------------------------------- | -------- | ------------------------------------------------------------------------- |
| [`G96` / `csson`](./03-prepwords-gcodes.md#g96-csson)   | gcode    | Switches Constant Surface Speed (CSS) mode on for spindle 1.              |
| [`G97` / `cssoff`](./03-prepwords-gcodes.md#g97-cssoff) | gcode    | Switches Constant Surface Speed (CSS) mode off for spindle 1.             |
| [`spinlimit`](./05-functions.md#spinlimit)              | function | Sets the maximum speed (in RPM) at which a spindle is allowed to revolve. |
| [`spindle`](./06-variables.md#spindle)                  | variable | The spindle speed word (`S`); sets the revolution speed of a spindle.     |

## Start / Stop

Each spindle may be started in either the clockwise or anti-clockwise direction, and is started and stopped using the following M-codes (or their equivalent mnemonics):

| Spindle | Clockwise start | Anti-clockwise start | Stop |
| --- | --- | --- | --- |
| Spindle 1 | `M3` / `spincw` | `M4` / `spinacw` | `M5` / `spinstop` |
| Spindle 2 | `M33` / `spincwss` | `M34` / `spinacwss` | `M35` / `spinstopss` |
| Spindle 3 | `M53` / `spincwsss` | `M54` / `spinacwsss` | `M55` / `spinstopsss` |
| Spindle 4 | `M73` / `spincwssss` | `M74` / `spinacwssss` | `M75` / `spinstopssss` |

## Joint Used As Spindle

A servo'd joint may be used as a spindle in certain cases. Of the four theoretically available spindles, each can correspond to one joint only, and this correspondence is determined when the machine is set up. Thus, for example, joint 4 may be issued with spindle 3 as its corresponding spindle; when the appropriate command is issued, the `C` axis (say) is treated as spindle 3.

The following commands enable the appropriate joints to be treated as spindles. The joints to which they correspond depend on the initial configuration of the machine, and so are not listed here.

| Enable joint as | M-code | Mnemonic |
| --- | --- | --- |
| Spindle 1 | `M26` | `spinen` |
| Spindle 2 | `M27` | `spinenss` |
| Spindle 3 | `M28` | `spinensss` |
| Spindle 4 | `M29` | `spinenssss` |

To switch the spindles back to joints, the following commands are used:

| Change back to joint | M-code | Mnemonic |
| --- | --- | --- |
| Spindle 1 | `M36` | `spindisab` |
| Spindle 2 | `M37` | `spindisabss` |
| Spindle 3 | `M38` | `spindisabsss` |
| Spindle 4 | `M39` | `spindisabssss` |

**Additional information:**

1. If the programmer leaves the spindle enabled after setting the spindle speed to 0 RPM, the axis may still turn slowly due to the open-loop nature of spindle control. It is advised to disable the spindle (switch back to joint control) when the spindle is not in use.
2. The spindle disable codes cause the programmed spindle speed to be set to zero.
3. Following a spindle disable code, the joint position (in machine and user frame coordinates) is truncated to remove multiples of 360 degrees. This is done using the machine offset facility.

## Spindle Speed

The role of the spindle speed word is to set the revolution speed of a particular spindle. There are two syntaxes for programming spindle speed.

The first syntax applies to spindles 1 to 4. It is programmed by the spindle speed name, which specifies the spindle to be affected, followed by either an expression in brackets or a number specifying the required speed. The spindle speed names are:

| Spindle | Speed word |
| --- | --- |
| Spindle 1 | `S` or `spindle` |
| Spindle 2 | `ss` or `spindless` |
| Spindle 3 | `sss` or `spindlesss` |
| Spindle 4 | `ssss` or `spindlessss` |

The second syntax applies to spindles 1 to 10. It is programmed by the spindle speed keyword `S` or `spindle`, followed by an expression in brackets specifying the spindle number, and then either a number or an expression in brackets specifying the required speed:

- `S(x) y` or `spindle(x) y`, where x is the spindle number and y is a literal spindle speed.
- `S(x)(y)` or `spindle(x)(y)`, where x is the spindle number and y is an expression giving the spindle speed.

The spindle speed is programmed in revolutions per minute (RPM) or feed per minute. The units of the programmed spindle speed depend on whether the CNC is in RPM or Constant Surface Speed (CSS) mode and on the inch/metric modal condition:

| Mode | Inch | Metric |
| --- | --- | --- |
| RPM mode | RPM | RPM |
| CSS mode | ft/min | m/min |

**Examples:**

```
ss2000        { set the speed of spindle 2 to 2000 revolutions per minute }
ssss (fv45)   { set the speed of spindle 4 to the value of fv45 }
S(1)(1000)    { set the speed of spindle 1 to 1000 revolutions per minute }
S(iv45)(fv45) { set spindle number (iv45) to the speed given by fv45 }
```

> [!NOTE]
> Programming a negative spindle speed is not valid and produces an error.

### RPM Mode

Each spindle may be individually programmed to be in RPM mode or Constant Surface Speed mode (see Constant Surface Speed Mode for programming details). When a spindle is in RPM mode, the programmed spindle speed word expresses the desired spindle speed in revolutions per minute (RPM).

### Constant Surface Speed Mode

As a tool cuts into a revolving workpiece, the circumference of the workpiece may be gradually reduced, decreasing the speed of the cutting tool relative to the surface of the workpiece. To keep this relative speed constant, the Constant Surface Speed (CSS) function increases the revolution speed of the workpiece as the tool cuts deeper. This function operates on any spindle but is normally only used on workpiece spindles. There are two commands for each spindle: one switches CSS mode on and the other switches it off.

| Spindle | Switch | Mnemonic | G-code |
| --- | --- | --- | --- |
| Spindle 1 | on | `csson` | `G96` |
| Spindle 1 | off | `cssoff` | `G97` |
| Spindle 2 | on | `cssonss` | `G196` |
| Spindle 2 | off | `cssoffss` | `G197` |
| Spindle 3 | on | `cssonsss` | `G296` |
| Spindle 3 | off | `cssoffsss` | `G297` |
| Spindle 4 | on | `cssonssss` | `G396` |
| Spindle 4 | off | `cssoffssss` | `G397` |

For spindles 5 to 10 the CSS G-codes are not predefined: they are configured by adding CSS G-code parameters (the on-code, the off-code and the per-spindle default mode, where 0 selects RPM mode and 1 selects CSS mode) to the parameter database. This is PLC and commissioning setup rather than part-program content; refer to the additional spindle documentation for the parameter names and values.

The current spindle speed is calculated from the machine position. In simple cases this radius is set up by the PLC; on more complex machines the equations for spindle radius must be set up during initial CNC commissioning.

> [!NOTE]
> CSS mode can cause dangerous increases in spindle speed if the tool is brought close to the centre of the workpiece. The `spinlimit` command (see Spindle Speed Limit) is provided to overcome this risk.

## Concurrent Spindle Ramping

After a spindle start code or a change in the spindle speed, the CNC may perform any rapid-mode movements to position the tool while the spindle is accelerating up to speed. When the CNC detects its first contour move (that is, a non-rapid move), it pauses (by setting the output logical ILB_WAIT) until the spindle has reached 80% of its programmed speed before continuing.

**Additional information:**

1. This feature depends on correct programming of the PLC.
2. The machine is never paused due to spindle ramping if the difference between the programmed and actual spindle speed (after overrides) is less than a threshold value (5 RPM).
3. Spindle velocity is not ramped through the deadband of ANCA velocity-controlled spindle drives because of a drive limitation (`*spindle_type: velocity`) in controlling spindle speeds below a minimum speed. The minimum controllable speed is specified by Sercos ID33006.

## Spindle Speed Override

Each spindle may have an override input (usually a potentiometer) that allows manual adjustment of the spindle speed. The spindle override is active in RPM and Constant Surface Speed modes unless the output logical `XOLB_SPINDLE_OVERRIDE_DISABLE_x` (where x is the spindle number, 1 to 10) has been set by the part program. Setting this output from a part program is PLC-level control; there is one such bit per spindle.

**Example:**

```
XOLB_SPINDLE_OVERRIDE_DISABLE_4 = on   { disable spindle override on spindle 4 }
```

> [!NOTE]
> If the CNC is in feed per revolution (`G95`) mode and the spindle override is set to zero, feed is inhibited.

## Gear Changing

To increase the spindle speed, a machine may need (depending on the machine) to pass through one or more gear changes. If these are necessary, the range of each gear is fixed in the PLC. Provision is made for up to four alternative sets of ranges to be substituted as required.

The alternate range is selected by setting the appropriate output logical `XOLB_ALT_SPINDLE_SPEED_x` (where x is the spindle number, 1 to 4) to on.

**Example:**

```
XOLB_ALT_SPINDLE_SPEED_2 = on   { apply the second set of ranges }
```

> [!NOTE]
> Gear changing requires the PLC to be correctly programmed for this feature.

## Spindle Speed Limit

As the tool gets closer to the central axis of a revolving workpiece, the workpiece has to spin faster to maintain a constant surface speed. To prevent the machine attempting to turn the spindle at an excessive speed, a `spinlimit` value is programmed, setting the maximum speed (in RPM) at which the workpiece is allowed to revolve. There are two syntaxes for setting the spindle speed limit.

The first syntax applies to spindles 1 to 4. The command relevant to the chosen spindle is programmed, followed by the value of the desired limit:

| Spindle | Command |
| --- | --- |
| Spindle 1 | `spinlimit` |
| Spindle 2 | `spinlimitss` |
| Spindle 3 | `spinlimitsss` |
| Spindle 4 | `spinlimitssss` |

The second syntax applies to spindles 1 to 10. It is programmed by the keyword `spinlimit` followed by an expression in brackets specifying the spindle number, then either a number or an expression in brackets specifying the spindle speed limit:

- `spinlimit(x)y`, where x is the spindle number and y is a literal spindle speed limit.
- `spinlimit(x)(y)`, where x is the spindle number and y is an expression giving the spindle speed limit.

**Examples:**

```
spinlimitss 5000   { maximum of 5000 RPM for the workpiece set up as spindle 2 }
spinlimit(2)5000   { maximum of 5000 RPM for the workpiece set up as spindle 2 }
```

**Additional information:**

1. The command is not a standard word and is not a standard block modifier. It should be programmed in a block by itself.
2. This spindle limit also applies to RPM mode and to spindle overrides.

## Spindle Orientation

Each spindle may have a spindle orientation position specified in the database, and the spindle moves to this position when its orientation command is programmed. For example, a spindle may have its zero angular position set in the database, in which case it rotates to zero degrees when its orientation command is programmed. One common use for spindle orientation is to align the spindle in preparation for a tool change.

Spindle orientation is performed via the following M-codes:

| M-code | Mnemonic | Description |
| --- | --- | --- |
| `M19` | `spinorient` | Orientate spindle 1 |
| `M20` | `spinorientss` | Orientate spindle 2 |
| `M21` | `spinorientsss` | Orientate spindle 3 |
| `M22` | `spinorientssss` | Orientate spindle 4 |

**Additional information:**

1. Spindle orientation may only be performed on spindles with some form of position feedback. These commands also require that the PLC has been appropriately programmed.
2. Generally the spindle is disabled once it reaches its orientation position.
