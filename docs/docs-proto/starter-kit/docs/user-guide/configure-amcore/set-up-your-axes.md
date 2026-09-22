# Set up your axes

**In this section**

This section provides explanations and instructions to assist you in configuring the kinematics in AMCore to match that of your machine.

## Understand the kinematics of AMCore

Before you continue, it is important that you understand the kinematic arrangement of AMCore. By default, AMCore includes a fixed kinematic mapping between joint and axis index, which is described here.

> [!TIP]
> To find out more about using alternate kinematic mappings, contact your ANCA Motion representative.

Joints are the actuators of the machine; think of the motor attached to a drive. They are numbered from 1 to 48. Each joint has a defined axis index and default axis label and is listed below.

|                        |     |     |     |     |     |     |     |     |     |     |
| ---------------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **Joint**              | 1   | 2   | 3   | 4   | 5   | 6   | 7   | 8   | 9   | 10  |
| **Axis index**         | 0   | 1   | 2   | 3   | 4   | 5   | 9   | 10  | 11  | 12  |
| **Default axis label** | X   | Y   | Z   | U   | V   | W   | A   | B   | C   | X'  |

|                        |     |     |     |     |     |     |     |     |     |     |
| ---------------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **Joint**              | 11  | 12  | 13  | 14  | 15  | 16  | 17  | 18  | 19  | 20  |
| **Axis index**         | 13  | 14  | \-  | 6   | 7   | 8   | 17  | 15  | 16  | 18  |
| **Default axis label** | Y'  | Z'  | SLV | P   | Q   | R   | A'  | U'  | V'  | B'  |

|                        |     |     |     |     |     |     |     |     |     |     |
| ---------------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **Joint**              | 21  | 22  | 23  | 24  | 25  | 26  | 27  | 28  | 29  | 30  |
| **Axis index**         | 20  | 21  | 22  | 23  | 24  | 25  | 26  | 27  | 28  | 29  |
| **Default axis label** | W'  | P'  | Q'  | R'  | A1  | B1  | C1  | P1  | Q1  | R1  |

|                        |     |     |     |     |     |     |     |     |     |     |
| ---------------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **Joint**              | 31  | 32  | 33  | 34  | 35  | 36  | 37  | 38  | 39  | 40  |
| **Axis index**         | 30  | 31  | 32  | 33  | 34  | 35  | 36  | 37  | 38  | 39  |
| **Default axis label** | U1  | V1  | W1  | X1  | Y1  | Z1  | A2  | B2  | C2  | P2  |

|                        |     |     |     |     |     |     |     |     |
| ---------------------- | --- | --- | --- | --- | --- | --- | --- | --- |
| **Joint**              | 41  | 42  | 43  | 44  | 45  | 46  | 47  | 48  |
| **Axis index**         | 40  | 41  | 42  | 43  | 44  | 45  | 46  | 47  |
| **Default axis label** | Q2  | R2  | U2  | V2  | W2  | X2  | Y2  | Z2  |

## Assign axis label

Users can modify the axis label to any desired axis index, as long as there is no duplication of the labels. This feature allows users to customize the labeling of the axis according to their preference.

```
*Axis.Axis_label: NOT_USED
*1.axis_label : U # X
*4.axis_label : X # U
```

You can use any combination of these axis labels, with the only restrictions being:

- Ordinate 1, 2, and 3 must be linear, perpendicular and follow the right-hand rule.
- The SLV axis is only to be used as the slave axis in a gantry.

## Assign devices to axes

First, you need to decide which axis label you will use for each device. You should have set the [Device name](../reference/parameter-reference.md#ethercat) parameter to reflect this when you [set up your devices](./set-up-your-devices/set-up-your-devices.md#set-up-your-devices).

To map the device to the axis:

1. Find the joint number of the axis from the table above.
2. Determine the logical address of the device (it was set when you [set up your devices](./set-up-your-devices/set-up-your-devices.md#set-up-your-devices)).
3. Set the [Joint logical device](../reference/parameter-reference.md#kinematics) for the joint to the logical address of the device.

## Set up logical machines

You can assign axes to different logical machines. All axes of a logical machine are synchronized. So, with multiple logical machines, you can control multiple machines asynchronously.

To map an axis to a logical machine:

1. Find the joint number of the axis from the table above.
2. Determine the logical machine number (1 to 3) of the machine that you want to control the axis.
3. Set the [Joint logical machine](../reference/parameter-reference.md#kinematics) parameter for the joint to the logical machine number.

## (Optional) Enable plane selection

If any of your logical machines have 3 perpendicular linear axes, you can enable the plane selection functions of EPPL that use of the mirroring, scaling and rotation EPPL functions on these axes.

To do this:

1. Determine which of the axes will correspond to the X, Y and Z axes of the plane selection functions. Make sure they follow the right-hand rule to avoid confusion.
2. Set the [Logical machine axes](../reference/parameter-reference.md#kinematics) parameter for the logical machine. The ordinates `x1`, `x2` and `x3` should be set to the axes you determined, respectively.

Now, you can select a plane on the logical machine and rotate, scale or mirror the commands. The axes X, Y and Z in the functions will correspond to the axes you configured, and will work analogously.

As a simple example, most machines will have the following parameters set:

```
1.x1.lm_map : X
1.x2.lm_map : Y
1.x3.lm_map : Z
```

This sets the ordinates for logical machine 1 to the X, Y and Z axes. So, selecting the XY plane (using `PLANEXY` EPPL command) in this logical machine will select the plane defined by the X and Y axes.

If the machine had another logical machine with 3 perpendicular, linear axes U, V and W:

```
2.x1.lm_map : U
2.x2.lm_map : V
2.x3.lm_map : W
```

Then, selecting the XY plane in logical machine 2 will select the plane defined by the U and V axes.