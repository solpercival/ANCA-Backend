# Velocity Profiling (VPI)

The Velocity Path Interpolator (VPI) calculates an estimate of interpolated points for the path, and the velocity (or feedrate) over the commanded path. Its three roles are captured in its name: 

**V**elocity: controls the velocity of the logical machine; 
**P**ath controls the position of the machine between the programmed points according to the interpolation mode (for example `linear`); 
**I**nterpolator splits a move into a time sequence of position and velocity commands. 

For example, a High Level Motion Command might instruct the VPI to move from (X, Y) = (0, 0) to (X, Y) = (100, 200) in linear interpolation mode; the VPI turns that move into a high-speed stream of interpolated axis vectors. The VPI functions between non-real-time and real-time processing in the principal data flow of the motion controller and is the primary control gate between the IO Control Block and the Motion Control Block. It monitors and responds in real time to IO state changes and events -- feed-hold button presses, feedrate override adjustment, MPG feed adjustments, cancel look-ahead events, cycle start, single block, M-code handshaking and conditional move completion. The VPI is one of the most important and complex modules in the machine controller.

**Commands and Variables**

| Name                                                          | Type  | Description                                                                         |
| ------------------------------------------------------------- | ----- | ----------------------------------------------------------------------------------- |
| [`G0` / `rapid`](./03-prepwords-gcodes.md#g0-rapid)           | gcode | Rapid interpolation mode: repositions the machine as quickly as possible.           |
| [`G1` / `linear`](./03-prepwords-gcodes.md#g1-linear)         | gcode | Linear interpolation mode.                                                          |
| [`G2` / `arccw`](./03-prepwords-gcodes.md#g2-arccw)           | gcode | Clockwise circular (and helical) interpolation mode.                                |
| [`G3` / `arcacw`](./03-prepwords-gcodes.md#g3-arcacw)         | gcode | Anti-clockwise circular (and helical) interpolation mode.                           |
| [`G4` / `dwell`](./03-prepwords-gcodes.md#g4-dwell)           | gcode | Pauses the machine for a specified time before executing the next block.            |
| [`G60` / `splineon`](./03-prepwords-gcodes.md#g60-splineon)   | gcode | Enables spline interpolation mode.                                                  |
| [`G61` / `splineoff`](./03-prepwords-gcodes.md#g61-splineoff) | gcode | Disables spline interpolation mode.                                                 |
| [`G95` / `feedupr`](./03-prepwords-gcodes.md#g95-feedupr)     | gcode | Selects feed-per-revolution mode, causing the VPI to interrogate the spindle speed. |

## Feedrate Smoothing Filter (FSF)

High levels of jerk in the feedrate (the second derivative of feedrate) can result in premature mechanical wear, or in sudden changes to position signals that are difficult for the servo drive controllers to track. The VPI can shape output feedrates using filters; the VPI Feedrate Smoothing Filter (FSF) is designed to address acceleration and jerk limits.

The FSF lets the user explicitly set the maximum allowed acceleration and jerk in feedrate output from the VPI by selecting the following parameters in `p_gen.db` or a higher-level configuration file:

| Parameter | Comment | Default | Example |
| --- | --- | --- | --- |
| `smooth_velocity_ramping` | Existing parameter used to enable the existing parabolic solution. | On (5DX) | Off |
| `ppp_num.order` | Defines which filter to use (must be set). | -- | 9 |
| `ppp_num.zero_level` | Defines the filter zero level (must be set). | -- | 0.000001 |
| `ppp_num.use_IIR_filter` | Enables the filter. | Off | On |
| `ppp_num.acceleration_bandwidth` | The signal frequency above which the acceleration magnitude is attenuated. Unit is radians per second. | 300 | 20 |
| `ppp_num.jerk_bandwidth` | The signal frequency above which the jerk magnitude is attenuated. Unit is radians per second. | 300 | 20 |

## Interpolation Modes

The Velocity Path Interpolator has control over the following basic interpolation modes:

- `rapid`
- `linear`
- circular and helical (`arccw` / `arcacw`)
- `spline`, and
- joint.

There are also position and velocity interpolation modes that are not core interpolators of the VPI. These interpolators have one or other of the following characteristics: they either have axis motion tightly coupled with spindle rotation, or overlay motion superimposed on the normal VPI interpolated motion.

### Feed per Revolution Mode

Feedrate is normally programmed in units per minute (for example 1000 mm/min). The AMCore CNC also supports programming of feedrate in units per revolution (for example 1 mm/rev), which causes the VPI to interrogate the spindle speed when calculating a target velocity. The DSC routes the actual spindle velocity back to the VPI using specific `xolf` variables.

> [!NOTE]
> Because of delays in the processing chain from the interpolators to the feedback of actual spindle velocity, this form of feedrate specification may not react fast enough for highly coupled motion such as threading on a lathe.

### TG CAM Moves

The original application of this type of move was CAM grinding. A TG CAM move bypasses all of the normal PPI / VPI path construction and control algorithms and provides the EPPL programmer with an interface to program the contour position of each axis for each machine update period. This tremendous level of flexibility comes with some onerous requirements as well: the CAM part programmer must manage the acceleration / deceleration profile for the CAM, and must program each axis position for each time increment. This type of motion is often referred to as "Electronic Gearbox" motion, because it simulates the very tight coupling of axis motion generated by specialised production equipment built with mechanically coupled axis drives. A simpler way of creating an electronic gearbox is to use the Electronic Cam function on the CNC, and to use TG CAM moves only when greater control of the position contour is required.

A TG CAM move is built one tick at a time by the EPPL programmer using the `tg_cam_write` BIF, and the motion is executed by calling the `tg_cam` BIF. There are a number of limitations when using TG CAM moves (for example, feedrate override will not work).

Because normal feedhold is disabled for TG CAM moves, it was determined that some form of emergency feedhold functionality should be incorporated into the TG CAM move processor. The AMCore TG CAM move processor therefore also provides emergency feedhold / stop capability during CAM profiling.

## Path Interpolator

The Path Interpolator (PI) calculates the LM Axis Vector based on the current move type, the current move's equations of motion and the Distance To Go, which has been calculated by the Velocity Interpolator (VI). The PI performs its work in the selection frame of reference.

One point to note about path interpolation is that for spline interpolation the interpolation parameter is not directly proportional to distance along the arc and the move. A 1 mm change in Distance To Go may map to more or less than a 1 mm displacement of the Axis Vector, depending on the curvature and parameterisation technique of the curve segment. The effect is that splined moves may vary in feedrate from the desired value; a side effect is that splined moves automatically slow down in regions of high curvature.

The combined effects of the Geom process (of the path planning filters), the Velocity Interpolator and the Path Interpolator distribute the interpolated feedrate amongst the axes of the move in N-vectorial space, according to the algorithms and the equations of motion of the move.

## Joint Space Velocity

Whilst the introduction of machine kinematics into the CNC architecture has simplified the path planning for many classes of machine, it can, in some situations, complicate the velocity planning. Since there is (usually) a non-linear relationship between the Axis Vector and the Joint Vector, the relationship between the rate of change of the Axis Vector (defined by the current interpolation feedrate and the equations of motion of the current move) and the rate of change of the Joint Vector is also non-linear.

### Rapid Mode Preview

Rapid mode interpolation repositions the machine as quickly as possible, ready for the next cutting move. The general rule for determining the target feedrate for a rapid move is that at least one of the joints should reach its maximum velocity during the move.

Rapid Mode Preview is used to estimate the highest feedrate possible. At the start of a rapid move, the Rapid Mode Preview module calculates a directional unit vector corresponding to the direction of the move (that is, of length 1 mm). The resultant vector is the joint-space displacement vector required to move by the unit vector in Cartesian space; this vector will be non-unit in length. The time taken to traverse this joint vector at each joint's maximum velocity determines the maximum time for this 1 mm move. Using the equation V = D / T, the path velocity is just the inverse of this time. A similar approach is used to determine path acceleration and path deceleration.

In some circumstances Rapid Mode Preview may still result in over-speeding, in which case the NC programmer may need to break up long rapid moves to avoid over-speeding.
