# Configure machine motion

This section helps you configure the parameters that control the motion of the machine.

## Configure scaling

Scaling defines the user-defined units in which joint data (e.g. positions) is sent to and received from the corresponding drives, over the fieldbus.

Each drive will use its own scaling parameters (e.g. "Factor group" per IEC61800-7-2 standard) to convert between these user-defined units and the drive's internal units (e.g. encoder increments). You must therefore configure AMCore's scaling for each joint to be consistent with the scaling configured on the corresponding drive, so they have common definitions of the units in which data is transmitted over the fieldbus.

To configure scaling, you need to set the following parameters for each joint:

- [Joint linear position scaling unit](../../reference/parameter-reference.md#scaling)
- [Joint rotary velocity scaling unit](../../reference/parameter-reference.md#scaling)

## Constrain the joints

Before you can command a movement safely, you need to define the range of motion for each joint.

So, you need to set the following parameters for each joint:

- [Joint lower soft limit](../../reference/parameter-reference.md#joint-limits)
- [Joint upper soft limit](../../reference/parameter-reference.md#joint-limits)
- [Joint soft limits deceleration limit](../../reference/parameter-reference.md#joint-limits)
- [Joint velocity limit](../../reference/parameter-reference.md#joint-limits)
- [Joint acceleration limit](../../reference/parameter-reference.md#joint-limits)
- [Joint deceleration limit](../../reference/parameter-reference.md#joint-limits)
- [Joint jerk limit](../../reference/parameter-reference.md#joint-limits)

> [!TIP]
> For the best performance, set the jerk limit to the largest jerk that the bandwidth of the joint allows, resulting in shorter execution times for rapid moves.

Once you've done this, you should be able to command each axis to change position. The commands AMCore generates for each joint will not exceed these limits.

> [!CAUTION]
> This doesn't mean it is safe to move! Erroneous commands could result in a collision. Always use the feedrate override when uncertain, and keep your hand on the emergency stop!

It's important to note that configuring the above joint limits also configures the calculated feedrate of rapid moves. Rapid moves are moves that attempt to move the end effector as fast as possible (regardless of the *configured* feedrate), and are typically used when re-positioning the machine. In a rapid move, at least one joint involved will reach the velocity limit given sufficient time, and all the joints will be commanded at the acceleration, deceleration and jerk limits.

So, now that the joint limits are appropriately set, you should be able to command rapid moves.

## Set nominal radii

A nominal radius for a rotary axis defines the effective radius of the axis. It is used to convert units from rotational to linear.

You have to set the nominal radii correctly so that the generated motion for combinations of linear and rotary joints will not exceed their motion limits.

To set the nominal radius for a rotary axis, set the [Nominal radius](../../reference/parameter-reference.md#kinematics) parameter for the axis.

## Constrain the end effector

Now, you should configure the limits that constrain the motion during normal operation.

To do this, set the following parameters:

- [Velocity limit](../../reference/parameter-reference.md#motion-limits)
- [Tangential acceleration limit](../../reference/parameter-reference.md#motion-limits)
- [Tangential deceleration limit](../../reference/parameter-reference.md#motion-limits)
- [Radial acceleration limit](../../reference/parameter-reference.md#motion-limits)
- [Tangential jerk limit](../../reference/parameter-reference.md#motion-limits)
- [Radial jerk limit](../../reference/parameter-reference.md#motion-limits)
- [Transitional jerk limit](../../reference/parameter-reference.md#motion-limits)

> [!TIP]
> Many of these parameters have corresponding `ORIDE` variables that can help you quickly change the value without restarting AMCore. This allows you to quickly iterate to an appropriate value.

These limits will apply during all motion, excluding rapid moves. 

Once you've set them appropriately, you should be able to run part programs and begin producing parts.

## Set alternative velocity limits

Depending on your application, you can use the primary and secondary rapid-limits to programmatically switch to alternate velocity limits at run-time.

The primary rapid-limit takes effect when the variable `ILB_RAPID_LIMIT` is active, and the secondary rapid-limit takes effect when the variable `ILB_RAPID_LIMIT_2` is active.

To set your alternative velocity limits, set the following parameters:

- [Joint rapid-limit velocity limit](../../reference/parameter-reference.md#joint-limits)
- [Rapid-limit velocity limit](../../reference/parameter-reference.md#joint-limits)
- [Secondary rapid-limit velocity limit](../../reference/parameter-reference.md#joint-limits)

> [!TIP]
> If a motion monitoring system is fitted to the machine, you should set the joint rapid-limit velocity limit such that there is some margin allowed for noise, etc.

## Set error thresholds

You can define the amount of position lag which, when exceeded, causes an error. This means the machine will be disabled and an error message will appear.

> [!NOTE]
> The position lag is the distance between the commanded position and the measured position.

To do this, set the [Joint position lag error threshold](../../reference/parameter-reference.md#motion-control). A suitable value is approximately 120% of the following lag (`G_SERVO_PE`) observed during a maximum velocity move.

You can also set a similar threshold in the velocity loop of the drive. This way, a potential error will be detected much quicker because:

- Drives inherently have a faster response time, and
- You don't have to wait for position error to accumulate.

To set this, use the drive parameter (32978) Velocity Following Error Threshold.

> [!NOTE]
> Refer to the firmware documentation for more information on this drive parameter.
> See [Set up a drive](../set-up-your-devices/set-up-a-drive.md#set-up-a-drive) to learn how to set drive parameters in a parameter file.

## Refine machine motion

The following features and parameters can be used to adjust the way that the tool path is processed and to fine-tune the machine.

### Smoothing filter

You can use the smoothing filter to smooth the position command stream sent to the servo drives. See [Smoothing filter](./smoothing-filter/smoothing-filter.md#smoothing-filter) to learn about the smoothing filter and its configuration.

### Tangency angle

`tangency_angle` database parameter (see [Tangency angle](../../reference/parameter-reference.md#motion-control)) defines the angle between successive moves that, when exceeded, causes the machine to pause between the moves. This means the machine decelerates to zero velocity before executing the next move.

If the angle is lower than this parameter value, the machine won't stop, but may slow down depending on the angle, curvature difference, transition jerk limit and the corner tolerance.

> [!NOTE]
> This parameter does not affect rapid moves. The machine always stops before *and* after a rapid move.

Increasing the tangency angle prevents the machine from coming to a complete stop at corners (decreasing cycle time), but may reduce the sharpness of the corner.

### Corner rounding limit

corner\_tol database parameter (see [Corner rounding limit](../../reference/parameter-reference.md#motion-control)) specified the corner rounding limit. When transitioning between moves (except splines), the corners may be rounded by an amount less than or equal to this parameter. The rounding only occurs when the tangency angle is not exceeded.

> [!NOTE]
> For rotary axes, the nominal radius is used (`nomrad`) to convert from degrees to millimetres.

Increasing the corner rounding limit will reduce the sharpness of the corner and can decrease the cycle time, since traversing a rounded corner can be performed at a higher feedrate without exceeding the motion limits.

### Move aligning

In some part programs the numbers are given with a low resolution. In some case, only two digits after the decimal place are used. Consider the below part program:

```
G0 X0 Y0  
G1 X1.50 Y1.50  
G1 X3.00 Y2.99
```

Since only two digits are used after the decimal point, rounding errors can be as large as 0.01mm. When AMCore processes the above part program, the two G1 moves do not look completely co-linear. The reason is that the slope of the first G1 move is 1.0, while the slope of the second G1 move is 0.99333. AMCore sees this as a small change in direction and depending on the transition jerk limit may slow down at the transition. Move aligning is used to align the moves in cases like this example and prevent slow downs. The below three parameters are used to configure move aligning:

- [Move aligning tolerance](../../reference/parameter-reference.md#motion-control)
- [Move aligning tolerance for reposition moves](../../reference/parameter-reference.md#motion-control)
- [Move aligning buffer size](../../reference/parameter-reference.md#motion-control)

## Refine MPG motion

The MPG hand-wheel is an incredibly useful tool for manually controlling the machine.

It's behaviour is configured by these parameters:

- [MPG velocity limit](../../reference/parameter-reference.md#mpg)
- [MPG gain](../../reference/parameter-reference.md#mpg)
- [MPG bias](../../reference/parameter-reference.md#mpg)
- [MPG position lag limit](../../reference/parameter-reference.md#mpg)
- [MPG axis position lag limit](../../reference/parameter-reference.md#mpg)
- [MPG input window](../../reference/parameter-reference.md#mpg)
- [MPG live offset input window](../../reference/parameter-reference.md#mpg)

The default values will work for most situations. You may, however, need to adjust the position lag limit parameter, which defines how far the actual position of the axis can lag behind the generated position command.

> [!NOTE]
> The position lag limit only comes into effect when the velocity limit is active. This is because when the velocity is limited, the actual position begins to lag.

If the position lag limit is too high (and you command a move faster than the velocity limit), you will find that after you stop moving the MPG wheel, the axis keeps moving.

If the position lag limit is too low, you could find that commanding small movements with a precise number of pulses won't move as far as you expect. This is because to limit the lag, pulses that cause the lag limit to be exceeded are discarded. This indirectly limits the MPG velocity. You can determine this effective velocity limit (in mm/min) by calculating: 60 x jerk<sup>1/3</sup> x lag<sup>2/3</sup>

> [!TIP]
> You can lower the position lag limit for a single axis using the MPG axis position lag limit parameter. This is useful for small axes, for which the shared lag limit is large relative to the axis dimensions.