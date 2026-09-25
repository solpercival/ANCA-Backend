# Feedrate

This guide gives a general overview of the structure of feedrate setting. The programmed feedrate affects all interpolation modes except `rapid` interpolation.

**Commands and Variables**

| Name                                                                                         | Type     | Description                                                                  |
| -------------------------------------------------------------------------------------------- | -------- | ---------------------------------------------------------------------------- |
| [`G67` / `nomrad`](./03-prepwords-gcodes.md#g67-nomrad)                                      | gcode    | Sets the nominal radius used in feedrate derivation for rotary axes.         |
| [`G93` / `feedinv`](./03-prepwords-gcodes.md#g93-feedinv)                                    | gcode    | Selects inverse time feedrate mode.                                          |
| [`G94` / `feedupm`](./03-prepwords-gcodes.md#g94-feedupm)                                    | gcode    | Selects feed per minute mode.                                                |
| [`G95` / `feedupr`](./03-prepwords-gcodes.md#g95-feedupr)                                    | gcode    | Selects feed per revolution mode.                                            |
| [`G150` / `feedvpvl`](./03-prepwords-gcodes.md#g150-feedvpvl)                                | gcode    | Selects virtual path velocity-length feedrate mode.                          |
| [`G195` / `feeduprss`](./03-prepwords-gcodes.md#g195-feeduprss)                              | gcode    | Selects feed per revolution mode for spindle 2.                              |
| [`G295` / `feeduprsss`](./03-prepwords-gcodes.md#g295-feeduprsss)                            | gcode    | Selects feed per revolution mode for spindle 3.                              |
| [`G395` / `feeduprssss`](./03-prepwords-gcodes.md#g395-feeduprssss)                          | gcode    | Selects feed per revolution mode for spindle 4.                              |
| [`feedgroup`](./05-functions.md#feedgroup)                                                   | function | Selects which axes are included in the feedrate calculation.                 |
| [`unitcv`](./05-functions.md#unitcv)                                                         | function | Converts a value between measurement units when programming joint feedrates. |
| [`feedrate`](./06-variables.md#feedrate)                                                     | variable | Sets the tool feedrate (the `F` word).                                         |
| [`g_actual_feedrate`](./06-variables.md#g_actual_feedrate)                                   | variable | Reports the actual feedrate of the executing move.                           |
| [`g_est_actual_virtual_path_velocity`](./06-variables.md#g_est_actual_virtual_path_velocity) | variable | Reports the estimated actual virtual path velocity.                          |
| [`g_virtual_path_length`](./06-variables.md#g_virtual_path_length)                           | variable | Reports the commanded virtual path length of the executing move.             |
| [`g_virtual_path_velocity`](./06-variables.md#g_virtual_path_velocity)                       | variable | Reports the commanded virtual path velocity of the executing move.           |
| [`vpl`](./06-variables.md#vpl)                                                               | variable | Sets the virtual path length for the current move.                           |
| [`vpv`](./06-variables.md#vpv)                                                               | variable | Sets the virtual path velocity for the current move.                         |

## Feedrate Words

The role of the feedrate words is to set the feedrate of the tool. The units of the feedrate words depend on the feedrate mode, which is described in Feedrate Modes.

When using feedrate mode `G93`/`feedinv`, `G94`/`feedupm` or `G95`/`feedupr`, the feedrate word is `F` or `feedrate`. When using feedrate mode `G150`/`feedvpvl`, the feedrate words are `vpv` and `vpl`.

For each feedrate word, feedrate programming consists of the feedrate word followed by either an expression in curved brackets or a number. The feedrate of the tool is set either implicitly by the value of the expression, or explicitly by the specific value of a number.

**Example:**

```
feedrate 2440 { sets the feedrate at 2440 units }
F (fv3 - 4 * fv18) { sets the feedrate at the value of the given expression }
```

## Feedrate Modes

There are four feedrate modes: feed per minute, feed per revolution, inverse time feedrate and virtual path velocity-length feedrate. The CNC interprets the programmed feedrate based on the feedrate mode. Feedrate mode commands are modal: once the mode is changed it stays at the new mode until the system is restarted or a new mode is commanded. The default mode at startup can be configured using the `feedrate_units.modal parameter`.

### Feed per Minute

Programmed with `G94` or `feedupm`. In this mode, the feedrate is specified in units per minute. The unit can be mm, inch or degrees, based on the selected measurement mode and move type. For example, if metric mode is selected and `G1 X100 F1000` is programmed, the CNC moves towards X100 with a feedrate of 1000 mm/min.

### Feed per Revolution

Programmed with `G95` or `feedupr`. In this mode, the feedrate is specified in units per revolution: the tool moves a certain distance along the programmed path for each revolution that a spindle makes. This involves specifying the desired spindle by programming the appropriate command. A feedrate of 0.01 in this mode means the tool moves 0.01 units (inches or mm) along the programmed path for each revolution of the spindle.

The command for the additional spindles is:

- Spindle 2: `G195` or `feeduprss`
- Spindle 3: `G295` or `feeduprsss`
- Spindle 4: `G395` or `feeduprssss`

For spindles 5 to 10, the feedrate units G-code is added to the parameter database, for example:

```
*spindle.5.feedrate_units_gcode : 495
```

### Inverse Time Feedrate

Programmed with `G93` or `feedinv`. In this mode, instead of specifying the velocity, the duration of the move is specified: the inverse of the desired duration of the move is given. The unit of the specified feedrate in this mode is 1/min. For example, `F10` means run the move in 1/10 of a minute, i.e. 6 seconds.

There are some restrictions when using inverse time feedrate:

- Standalone feedrate commands are not allowed, because the feedrate in this mode is the time that a move takes, and if no move is given the feedrate has no meaning. The only exception is in a `splineon` (`G60`) block.
- The feedrate must be specified with every move command (except for rapid moves).
- `feedgroup` commands are ignored, because in this mode the time of the movement is specified and the time should not change.
- `fillet` and `chamfer` commands cannot be used.
- Smoothing fillets cannot be used.
- Cutter radius compensation (CRC) cannot be used.
- B-splines cannot be used.

When switching from `G93` to `G94` or `G95`, the last calculated feedrate is used. For example, in the part program below the move at line N05 has a programmed feedrate of 1000 mm/min: at line N03 the move length is 100 mm and the time to perform the move is 1/10 of a minute, so the feedrate is calculated as 1000 mm/min. At line N04 the mode changes to `G94`, and at line N05 the last calculated feedrate, 1000 mm/min, is used.

**Example:**

```
N01 G93
N02 G0 X0
N03 G1 X100 F10
N04 G94
N05 G1 X200
```

### Virtual Path Velocity-Length Feedrate

Programmed with `G150` or `feedvpvl`. This mode is an extension of `G93`/`feedinv`. Instead of providing the desired duration of the move as inverse time using the `F` or `feedrate` command, it uses two commands:

- `vpv` -- virtual path velocity
- `vpl` -- virtual path length

The virtual path is a path of interest to the user and represents the trajectory that the application layer is controlling; AMCore does not inherently know this path. For example, the grinding path in a 5-axis machine can be referred to as a virtual path. `vpv` is the desired velocity and `vpl` is the move length along this path. Given `vpv` and `vpl` commands for a move, the desired duration for the machine to complete the move is `vpl`/`vpv`. Using this, AMCore internally calculates the appropriate machine feedrate for that move.

The following variables are available in this feedrate mode:

- `g_virtual_path_velocity` shows the commanded `vpv` value of the executing move.
- `g_virtual_path_length` shows the commanded `vpl` value of the executing move.
- `g_est_actual_virtual_path_velocity` shows the estimated actual virtual path velocity. If the machine path and virtual path are linearly related, this matches the actual virtual path velocity; when using sophisticated kinematics and/or rotary joints, it closely matches the actual virtual path velocity only when the move displacements are small.

The units for `vpv` and `vpl` are based on the selected measurement mode (`G70`/`G71`). In metric mode (`G71`), `vpv` is in mm/min and `vpl` is in mm. In inch mode (`G70`), `vpv` is in inches/min and `vpl` is in inches. `g_virtual_path_length` is always in mm, and `g_virtual_path_velocity` and `g_est_actual_virtual_path_velocity` are always in mm/min.

The following restrictions apply when using this feedrate mode:

- F and `feedrate` commands cannot be used in this feedrate mode (in other feedrate modes, `vpv` and `vpl` commands cannot be used).
- Every move command must have both a `vpv` and a `vpl` command (except rapid moves).
- `vpl` cannot be zero.
- Standalone `vpv` and `vpl` commands are not allowed, as these commands represent duration and have no meaning without an associated move. The only exception is in a `splineon` (`G60`) block.
- `feedgroup` commands are ignored because the movement time is specified in this mode and should not change.
- `fillet` and `chamfer` commands cannot be used.
- Smoothing fillets cannot be used.
- Cutter radius compensation (CRC) cannot be used.
- B-splines cannot be used.

When switching from `G150` to `G94` or `G95`, the last calculated machine feedrate is used, as explained in Inverse Time Feedrate.

**Example:**

Assuming metric mode, in block N03 the user wants to move a length of 0.2 mm at a velocity of 20 mm/min along the virtual path. This is equivalent to a desired duration of 0.01 minutes. The machine move length on the `X` axis is 0.3 mm, so the commanded machine feedrate is 0.3 / 0.01 = 30 mm/min. When block N03 is executing, `g_actual_feedrate` = 30 mm/min. `g_est_actual_virtual_path_velocity` is calculated using `g_actual_feedrate` x (`vpl` / machine move length), so `g_est_actual_virtual_path_velocity` = 30 x (0.2/0.3) = 20 mm/min.

```
N01 G150
N02 G0 X0
N03 G1 X0.3 VPV20 VPL0.2
```

## Linear Interpolation Feedrate Derivation

The feedrate programmed into a linear move is tangential to the linear path, and is the vector sum of feedrates parallel to the various axes in which the interpolation takes place. Thus if the interpolation takes place in the axes X, Y, A, B, C etc., the programmed feedrate is apportioned to the velocity along the various axes by the following relation:

$$F = \sqrt{F_{X}^{2} + F_{Y}^{2} + F_{Z}^{2} + F_{A}^{2} + F_{B}^{2} + F_{C}^{2} + \cdots}$$

where `F` is the programmed feedrate.

As moves in rotational axes involve degrees and not inches or millimetres, calculations are made to ensure smooth interpolation, where a degree is taken to be a certain length in millimetres in the calculation of the feedrate. If the machine is in inch mode, allowance is made for the difference in size in relation to millimetres.

Rotational axes have nominal radius parameters (<n>.`nomrad`). The nominal radius may be changed during run-time by programming the `nomrad` instruction. For feedrate derivation when interpolating one or more rotational axes (optionally with other linear axes), the AMCore CNC calculates a circular path traced by a point at the nominal radius away from the centre of the axis of rotation. This path is used in the calculation of the feedrate, instead of the angular displacement. A nominal radius of 57.29577951 mm will result in 1 mm/min = 1 degree/min.

**Example:**

```
{ Move along the X-axis to X=20. Between X=20 and X=40, rotate the A-axis to A=270 degrees, }
{ then move along the Y-axis to Y=20. The nominal radius for the A-axis is 100 mm. }
absolute
feedrate 80 { Total path feedrate of 80 mm/min }
X(0) Y(0) a(0)
X(20) { Fx = 80 mm/min, Fy = 0, Fa = 0 }
N1 a(270) X(40) { Fx = 3.39 mm/min, Fy = 0, Fa = 45.80 deg/min }
Y(20)
```

The equations for determining the feedrate breakdown for block n1 are as follows.

Programmed move:

$$\Delta X = 20\text{ mm}, \quad \Delta A_{\theta} = 270\text{ deg}, \quad F = 80\text{ mm/min}, \quad nomrad_{A} = 100\text{ mm}$$

Equivalent linear displacement of the rotary axis:

$$\Delta A = 2\pi \times nomrad_{A} \times \frac{\Delta A_{\theta}}{360} = 2\pi \times 100 \times \frac{270}{360} = 471.2389\text{ mm}$$

Programmed feedrate:

$$F = \sqrt{\left(\frac{\Delta X}{\Delta t}\right)^{2} + \left(\frac{\Delta Y}{\Delta t}\right)^{2} + \left(\frac{\Delta Z}{\Delta t}\right)^{2} + \left(\frac{\Delta A}{\Delta t}\right)^{2} + \left(\frac{\Delta B}{\Delta t}\right)^{2} + \left(\frac{\Delta C}{\Delta t}\right)^{2} + \cdots}$$

Time to execute the move:

$$F = \sqrt{\left(\frac{\Delta X}{\Delta t}\right)^{2} + \left(\frac{\Delta A}{\Delta t}\right)^{2}}$$

$$80 = \sqrt{\frac{(20)^{2}}{\Delta t^{2}} + \frac{(471.2389)^{2}}{\Delta t^{2}}}$$

$$80 = \frac{1}{\Delta t}\sqrt{(20)^{2} + (471.2389)^{2}}$$

$$\Delta t = \frac{1}{80}\sqrt{(20)^{2} + (471.2389)^{2}} = 5.8958\text{ min}$$

Joint feedrate:

$$F_{X} = \frac{\Delta X}{\Delta t} = \frac{20}{5.8958} = 3.39\text{ mm/min}$$

$$F_{A} = \frac{\Delta A}{\Delta t} = \frac{471.2389}{5.8958} = 79.93\text{ mm/min}$$

$$F_{A_{\theta}} = \frac{360 \times F_{A}}{2\pi \times nomrad_{A}} = \frac{360 \times 79.93}{2\pi \times 100} = 45.80\text{ deg/min}$$

## Circular Interpolation Feedrate Derivation

The derivation of circular and helical feedrate is similar to that for linear interpolation, except that the total distance is calculated as the square root of the sum of the squares of:

- the arc length around the circumference of the circular arc, and
- the linear length of any other axes included in a helical move.

## Spline Interpolation Feedrate Derivation

The derivation of feedrate for spline interpolation is similar to that for [Linear Interpolation Feedrate Derivation](#linear-interpolation-feedrate-derivation), except that at regions of high curvature the feedrate will reduce. High curvature may be produced by a high tension factor or by badly aligned control points.

## Joint Interpolation Feedrate Derivation

As only one joint may be interpolated at a time during joint interpolation, the programmed feedrate simply relates to joint units per minute (after scaling for inch/metric mode selection to mm/min).

**Example:**

```
{ To interpolate joint 2 to position 100mm at 500 mm/min }
F (unitcv(500))
joint 2,100
```

If F100 is programmed in inch mode, it is converted internally to 2540, so a revolute joint will move at 2540 degrees/min. If 100 degrees/min is the desired feedrate for a joint move, then the feedrate must be programmed as:

```
F (unitcv(100))
```

## Axis Selection for Feedrate Control

If the `feedgroup` command is followed by one or more dimension words, the CNC includes the corresponding axes in the feedrate calculation. If `feedgroup` is called without any dimension words, any previous `feedgroup` command is cancelled, and all axes in a move are then included in the feedrate calculation.

**Example 1:**

```
feedgroup X
G91 G1 X100 Y200 F100
```

In this example, the `X` axis moves at a feedrate of 100 mm/min. The `Y` axis moves at 200 mm/min so that both axes reach the target at the same time.

**Example 2:**

```
feedgroup
G91 G1 X100 Y200 F100
```

In this example, the `X` and `Y` axes together move at a feedrate of 100 mm/min. The feedrate of the `X` axis is about 45 mm/min and the `Y` axis moves at a feedrate close to 90 mm/min. The vector summation of their velocities equals 100 mm/min.

**Additional Information:**

1. `feedgroup` only affects linear and spline moves.
2. If none of the axes specified by the `feedgroup` command participate in a move, that move is performed ignoring the `feedgroup` command. For example, if `feedgroup X` is commanded, `G1 Y100 Z100 A90` will run as if `feedgroup` was never used.
