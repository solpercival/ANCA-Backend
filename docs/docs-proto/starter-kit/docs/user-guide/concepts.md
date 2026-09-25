# Concepts

This section introduces many important AMCore concepts that are used throughout the guide. It also provides links to further reading.

## Configuration properties

Configuration properties are settings that apply to the current AMCore session. You can set them by providing a configuration file to AMCore on startup.

You can override configuration properties from an existing configuration file, in order to customise an existing system.

All configuration properties are optional. If you don't set (or inherit) some properties, they will revert to their default values.

> [!NOTE]  
> To learn how to use configuration properties, go to the [Understand configuration properties section](./configure-amcore/understand-configuration-properties.md#understand-configuration-properties).  
> For a list of all available configuration properties, refer to the [Configuration property reference](./reference/configuration-property-reference.md#configuration-property-reference).

## Data block mapping

Data block mapping provides a configurable way to access data in the EtherCAT process data map for an EtherCAT drive. A Data Block Map defines the source, destination, size and state of the data to be transferred from the drive.

## Extended Part Programming Language (EPPL)

AMCore's Extended Part Programming Language (EPPL) is a superset of the ISO-6983 (G-Code) programming language. It includes familiar G-Codes, M-Codes, S-Codes, etc. but also includes many optional extensions which may be used to produce programs that are more powerful and easier to read. Some key features of EPPL are:

* Mnemonic names for G-codes
* Variables, if statements, for loops
* Spline interpolation
* Transformations (rotation, scaling, mirroring)

## Fieldbus

Fieldbus is the name of a family of industrial computer network protocols used for real-time distributed control, standardized as IEC 61158. For this user guide, these protocols are SERCOS and/or EtherCAT.

## Joint

A joint is an actuator of an axis. In AMCore, joints have an index from 1 to 48.

## Kinematics

Kinematics refers to the relationship between axis space (commanded by part programs) and joint space (commanded by AMCore).

> [!NOTE]
> See the [Set up your axes ](./configure-amcore/set-up-your-axes.md#set-up-your-axes) section to learn how to configure the kinematics in AMCore.

## Logical machine

A logical machine (LM) is a grouping of programmable dimension words (e.g. X, Y, Z) that may be operated in synchronization. It is an indivisible, non-shareable resource. The allocation of dimension words to logical machines is static, made once during system start-up.

## Manual Pulse Generator (MPG)

A Manual Pulse Generator (MPG) is the wheel component of ANCA Motion pendants. Turning the wheel generates position pulses that can be used to precisely move an axis. It can also be used to step through and rewind a part program.

## Move

A move refers to an AMCore command that makes the machine move. You can command the following move types:

| Type    | Description                                                                                                        |
| ------- | ------------------------------------------------------------------------------------------------------------------ |
| Rapid   | A move to a specified location as quickly as possible.                                                             |
| Linear  | A move to a specified location at the configured feedrate in a straight line.                                      |
| Helical | A move to a specified location at the configured feedrate by travelling in a circular arc.                         |
| Spline  | A move to a specified location at the configured feedrate in such a way that causes the overall path to be smooth. |
| Joint   | A special type of move in which you directly command the joints (rather than the axes).                            |

## Parameters

Parameters are persistent settings that apply to AMCore. They have a key and a value, separated by a colon.

The key is used to identify the parameter. Many keys begin with a modifier (e.g. `1.smoothing_factor`) that can be used to set the parameter in different domains (logical machines, joints, etc.). Omitting the modifier sets the parameter in all domains. For example:

```
# Set the safe_velocity for all joints to 1960
*safe_velocity: 1960

# Change the safe_velocity for joints 4 and 5
*4.safe_velocity: 17640
*5.safe_velocity: 186.2
```

A *parameter file* is a text file containing one or more parameters. There are 6 parameter files (listed in priority order): test, user, oem, mspec, common and gen.

> [!NOTE]
> You can provide one (or more) of these files (except gen) via the [Parameter files configuration properties](./reference/configuration-property-reference.md#parameters).

When AMCore queries a parameter, it searches the parameter files in priority order until it finds a match. This hierarchy is commonly referred to as "the database".

The *gen* parameter file contains default values for AMCore parameters, and is not configurable. For the list of AMCore parameters and their default values, refer to the [Parameter reference](./reference/parameter-reference.md#parameter-reference).

> [!NOTE]
> For a more detailed description of parameters and how to use them, see the [Understand parameters](./configure-amcore/understand-parameters.md#understand-parameters) section.

## Part programs

Also referred to as "NC programs", part programs are used to program machine movement. They are written in [EPPL](#extended-part-programming-language-eppl).

You can [run part programs](./use-amcore/run-part-programs.md#run-part-programs) via a number of different interfaces - including via EPPL G-Codes and M-Codes, or from your PLC or application code.

You can choose which folders AMCore searches for part programs (and the order in which they are searched) by [defining a part program search hierarchy](./configure-amcore/define-a-part-program-search-hierarchy.md#define-a-part-program-search-hierarchy)..

> [!NOTE]
> To learn the basics of writing part programs, go to the [Create part programs](./use-amcore/create-part-programs/create-part-programs.md#create-part-programs) section. To learn more advanced programming, refer to the EPPL Guide.

## Programmable Logic Controller (PLC)

In AMCore, a programmable logic controller (PLC) controls the input and output state variables. For example, when you press an emergency stop button, this is detected by the PLC which tells AMCore to disable the drives.

## Shared memory

Shared memory is precisely what it sounds like: memory that is shared. In particular, many AMCore processes use shared memory for inter-process communication. Effectively, variables in shared memory are global variables that anyone can read and write. 

## Variables

Commonly referred to as "shared memory variables", variables are named locations in shared memory that can be accessed by all parts of the system. They are typically used to monitor the state of the CNC or to change some aspects of machine behaviour until the next system restart.

> [!NOTE]
> For a list of variables available in AMCore, refer to the [Variable reference](./reference/variable-reference.md#variable-reference).

## Alarms

Alarms are entities that notify the machine operator of any abnormal system state. An alarm instance represents a single occurrence of that alarm. 

There are 2 types of alarms:

* Transient alarms: represent a temporary occurrence of an event, be it an application exception or warning for the operator.
* Enduring alarms:  represent a condition of a machine that persists over a period of time e.g., a temperature limit alarm, a low-level switch or soft limit condition. 
  * Latching alarms: alarms that are critical to the protection of human safety and the environment. Latching alarms that are raised must be reset before they can be raised again.

Some alarms may require acknowledgement/ confirmation to ensure that the condition leading to an alarm has been noticed/ addressed by the operator.