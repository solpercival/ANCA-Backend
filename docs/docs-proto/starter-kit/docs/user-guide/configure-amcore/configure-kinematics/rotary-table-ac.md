# Rotary Table AC

This kinematics can be used to control a machine with the standard X, Y and Z axis plus a rotary table with two rotary axes. The rotary axes on the table are A and C. The kinematics also supports three soft axes: U, V and W. When A and C are both at zero degrees, U is parallel to and in the same direction as X, V is parallel to and in the same direction of Y and W is parallel to and in the same direction as Z. UVW frame rotates around the X axis by A degrees and rotates around the Z axis by C degrees. Offsets to the UVW frame can be applied using the EFF command in EPPL.

## Product Code

In order to activate this kinematics, you need a purchase option called `Rotary Table AC` with product code 138. The kinematics can be used only if this purchase option is included in the license.

## Configuration

To activate this kinematics, use the below database setting.

```
*kinematics: rotarytable_ac
```