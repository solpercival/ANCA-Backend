# Bevel head type 1

This kinematics is used for a machine that has three linear hard axes (X, Y and Z), and two rotary hard axes (A and B) when B axis is mounted on the A axis. The cutting head is attached to the B axis. A soft axis called W is also supported.

The relationship between joint 1 (J1), joint 2 (J2), axis A, axis B and axis W is as follows.

&Delta;J1 = &Delta;W \* sin(B)  
&Delta;J2 = -&Delta;W \* sin(A) \* cos(B)

In this kinematics, joint 3 is not affected by W axis. Joint 1 is parallel to X axis, Joint 2 is parallel to Y axis and joint 3 is parallel to Z axis.

## Product code

In order to activate bevel head type 1 kinematics, you need a purchase option called "Bevel Kinematics Type1" with product code 135. The kinematics can be used only if this purchase option is included in the license.

## Configuration

To activate this kinematics use the below database setting.

`*kinematics: bevel_type1`

Two static offsets need to be specified. Set `effector.1.static_offset.x` to the distance from the centreline of the B axis to the centreline of the tool (or the laser beam). Set `effector.1.static_offset.y` to the distance from the centreline of the A axis to the centreline of the tool (or the laser beam).

## Programming

To enable bevel head kinematics, call `bevel_head_enable()` EPPL command. To disable bevel head kinematics, call `bevel_head_disable()` in the part program. You can see the current status of the bevel head kinematics using `G_BEVEL_HEAD_ENABLED` variable. This is a boolean variable and is set to `on` when the bevel head is enabled.

When enabling or disabling the bevel head, joint positions do not change and the machine does not move. However, the positions of one or more axes may change. See an example below.

## Pivot point

When the bevel head is enabled, if A or B axes are rotated, the CNC moves the linear joints of the machine so that the pivot point does not move in respect to the workpiece. Using EFF command in EPPL, the pivot point can be placed at the tip of the laser beam or at the end of the tool. See the example below to find out how the EFF command can move the pivot point.

## Example

### Configuration

```
*kinematics: bevel_type1
*effector.1.static_offset.x: 0.0
*effector.1.static_offset.y: 0.0

*1.lm_used: USED
*lm_num: 1

*1.servo_interp_order: SERVO_INTERP_ZOH
*2.servo_interp_order: SERVO_INTERP_ZOH
*3.servo_interp_order: SERVO_INTERP_ZOH
*6.servo_interp_order: SERVO_INTERP_ZOH
*7.servo_interp_order: SERVO_INTERP_ZOH
*8.servo_interp_order: SERVO_INTERP_ZOH

*lm_map: NOT_USED
*1.x1.lm_map: X
*1.x2.lm_map: Y
*1.x3.lm_map: Z
*1.x4.lm_map: W
*1.x5.lm_map: A
*1.x6.lm_map: B
*w.sa_jnt: 6
```

In the above configuration, `effector.1.static_offset.x` and `effector.1.static_offset.y` are both set to zero for simplicity. In reality these values should be configured as explained in [this section](#configuration).

### Programming

```
bevel_head_enable()
eff k-100
G1 A-45
```

Before running the part program, `G_BEVEL_HEAD_ENABLED` is `off`. The first line of the part program enables the bevel head and changes `G_BEVEL_HEAD_ENABLED` to `on`. At this stage, the pivot point is at the intersection of the centreline of the tool and the centreline of the B axis.

The second line, applies an offset of -100 to the W axis. This moves the pivot point 100 millimetres in the negative direction of the W axis. Up to this point, no physical movement has taken place since the pivot point is just an imaginary point in space.

The third line rotates A axis by 45 degrees. At the same time, the cutting head moves in the positive direction of the Y axis in order to keep the pivot point stationary in space. At the end of the move, joint 2 will be at 70.711mm and Y axis will have a value of zero. If `bevel_head_disable()` is commanded at this state, the position of joint 2 will not change and the machine will not move, but the position of Y axis will change to 70.711mm.