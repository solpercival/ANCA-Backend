# Variable reference

## Motion control

In the below table, writable variables with an LM scope need a `sync` command before changes take effect.

| Name, Scope, Type | Access | Units | Description |
| --- | --- | --- | --- |
| G\_SMOOTHING\_FACTOR<br>**Scope:** LM<br>**Type:** Integer | Read-Write | \-  | The strength of the joint smoothing filter (a low pass filter that smooths the commanded position).<br><br>Parameter: [Smoothing factor](../reference/parameter-reference.md#motion-control) |
| G\_SMOOTHING\_TYPE<br>**Scope:** LM<br>**Type:** Integer | Read-Write | \-  | Determines the type of the smoothing filter. Can be either 0 or 2.<br><br>Parameter: [Smoothing type](../reference/parameter-reference.md#motion-control) |
| G\_TANGENCY\_ANGLE<br>**Scope:** LM<br>**Type:** Float | Read-Write | deg | Defines the angle between successive moves that when exceeded cause the machine to pause between the moves.<br><br>Parameter: [Tangency angle](../reference/parameter-reference.md#motion-control) |
| G\_ACCEL<br>**Scope:** LM<br>**Type:** Float | Read-Write | mm/s<sup>2</sup> | Maximum acceleration of the end effector in the direction it is moving.<br><br>Parameter: [Tangential acceleration limit](../reference/parameter-reference.md#motion-limits) |
| G\_DECEL<br>**Scope:** LM<br>**Type:** Float | Read-Write | mm/s<sup>2</sup> | Maximum deceleration of the end effector in the direction it is moving.<br><br>Parameter: [Tangential deceleration limit](../reference/parameter-reference.md#motion-limits) |
| G\_RADIAL\_ACCEL\_LIMIT<br>**Scope:** LM<br>**Type:** Float | Read-Write | mm/s<sup>2</sup> | Maximum acceleration of the end effector caused by moving on a curved path.<br><br>Parameter: [Radial acceleration limit](../reference/parameter-reference.md#motion-limits) |
| G\_RADIAL\_ACCEL\_ORIDE<br>**Scope:** LM<br>**Type:** Float | Read-Write | %   | Scale factor applied to G\_RADIAL\_ACCEL\_LIMIT. |
| G\_JERK<br>**Scope:** LM<br>**Type:** Float | Read-Write | mm/s<sup>3</sup> | Maximum jerk of the end effector in the direction it is moving.<br><br>Parameter: [Tangential jerk limit](../reference/parameter-reference.md#motion-limits) |
| G\_JERK\_ORIDE<br>**Scope:** LM<br>**Type:** Float | Read-Write | %   | Scale factor applied to G\_JERK. |
| G\_RADIAL\_JERK\_LIMIT<br>**Scope:** LM<br>**Type:** Float | Read-Write | mm/s<sup>3</sup> | Maximum jerk of the end effector caused by moving on a curved path.<br><br>Parameter: [Radial jerk limit](../reference/parameter-reference.md#motion-limits) |
| G\_RADIAL\_JERK\_ORIDE<br>**Scope:** LM<br>**Type:** Float | Read-Write | %   | Scale factor applied to G\_RADIAL\_JERK\_LIMIT. |
| G\_TRANSITION\_JERK\_LIMIT<br>**Scope:** LM<br>**Type:** Float | Read-Write | mm/s<sup>3</sup> | Maximum jerk of the end effector during the transition from one move to the following move.<br><br>Parameter: [Transitional jerk limit](../reference/parameter-reference.md#motion-limits) |
| G\_TRANSITION\_JERK\_ORIDE<br>**Scope:** LM<br>**Type:** Float | Read-Write | %   | Scale factor applied to G\_TRANSITION\_JERK\_LIMIT. |
| G\_VIRTUAL\_PATH\_LENGTH<br>**Scope:** LM<br>**Type:** Float | Read-Only | mm  | Commanded `VPL` value in the executing move block.<br><br>Applicable only in `G150`/ `FEEDVPVL` feedrate mode. |
| G\_VIRTUAL\_PATH\_VELOCITY<br>**Scope:** LM<br>**Type:** Float | Read-Only | mm/min | Commanded `VPV` value in the executing move block.<br><br>Applicable only in `G150`/ `FEEDVPVL` feedrate mode. |
| G\_EST\_ACTUAL\_VIRTUAL\_PATH\_VELOCITY<br>**Scope:** LM<br>**Type:** Float | Read-Only | mm/min | Estimated actual virtual path velocity. If the machine path and virtual path are linearly related, this will match the actual virtual path velocity. However, when using sophisticated kinematics and/or rotary joints, this will closely match the actual virtual path velocity only when the move displacements are small.<br><br>Applicable only in `G150`/ `FEEDVPVL` feedrate mode. |
| G\_SERVO\_SLM\<j-1><br>**Scope:** CNC<br>**Type:** Float | Read-Write | mm or deg | Minimum position of joint \<j> (1 to 48, e.g. G\_SERVO\_SLM0 is for joint 1).<br><br>The joint must be within the new limits and capable of stopping before reaching them, otherwise an error will occur and the limit won't be applied.<br><br>Parameter: [Joint lower soft limit](../reference/parameter-reference.md#joint-limits) |
| G\_SERVO\_SLP\<j-1><br>**Scope:** CNC<br>**Type:** Float | Read-Write | mm or deg | Maximum position of joint \<j> (1 to 48, e.g. G\_SERVO\_SLP0 is for joint 1).<br><br>The joint must be within the new limit and capable of stopping before reaching it, otherwise an error will occur and the limit won't be applied.<br><br>Parameter: [Joint upper soft limit](../reference/parameter-reference.md#joint-limits) |
| G\_SERVO\_AP\<j-1><br>**Scope:** CNC<br>**Type:** Float | Read-Only | mm or deg | Actual position of joint \<j> (1 to 48, e.g. G\_SERVO\_AP0 is for joint 1). |
| G\_SERVO\_PREVIOUS\_TIME<br>**Scope:** CNC<br>**Type:** Float | Read-Only | s   | The time that G\_SERVO\_AP variables were updated, measured in seconds since AMCore started.<br><br>Resets to 0 at 31,622,400 (366 days). |
| G\_TARGET\_LIVE\_OFFSET\<n-1><br>**Scope:** CNC<br>**Type:** Float | Read-Write | mm or deg | Target live offset values axis n (1 to 48, e.g. G\_TRAGET\_LIVE\_OFFSET0 is for axis 1). AMCore will add this value to the position of the axis, provided that the maximum velocity limit of the affected joints in not exceeded. The current velocity of joints resulting from part program execution is taken into account.  <br>If adding live offsets results in any joint exceeding its maximum velocity limit, only a fraction of live offsets will be added.  <br>Live offsets for all axes will be applied synchronously, meaning that all axes get to their target values at the same time.  <br>The value of the applied live offset can be read from G\_COMMANDED\_LIVE\_OFFSET variable.  <br>  <br>When XILB\_EMERGENCY\_STOP is set, G\_TARGET\_LIVE\_OFFSET will be set to the value of G\_COMMANDED\_LIVE\_OFFSET.  <br>The same thing happens if one of the joints that would move due to the value assigned to G\_TARGET\_LIVE\_OFFSET hits its soft limit, i.e.  <br>the values in G\_COMMANDED\_LIVE\_OFFSET array will be written to G\_TARGET\_LIVE\_OFFSET array and subsequently,  <br>G\_COMMANDED\_LIVE\_OFFSET values will stop changing. |
| G\_COMMANDED\_LIVE\_OFFSET\<n-1><br>**Scope:** CNC<br>**Type:** Float | Read-Only | mm or deg | Commanded live offset values for axis number n. See description of G\_TARGET\_LIVE\_OFFSET for details. |
| G\_BEVEL\_HEAD\_ENABLED<br>**Scope:** CNC<br>**Type:** Boolean | Read-Only | \-  | Is On when bevel head is enabled and Off otherwise. |
| G\_BEVEL\_HEAD\_MODE<br>**Scope:** CNC<br>**Type:** Integer | Read-Only | \-  | Reflects the bevel head kinematics mode. The mode can be changed using `bevel_head_mode` EPPL command.<br><br>See `bevel_head_mode` parameter in parameters reference and part programmers reference manual for more information. |
| G\_PIVOT\_POINT\_FEEDRATE<br>**Scope:** CNC<br>**Type:** Float | Read-Only | mm/min | Reflects the velocity of the pivot point. This variable is currently applicable only to bevel\_type1 kinematics. See [this page](../configure-amcore/configure-kinematics/bevel-head-type-1.md#bevel-head-type-1) for information about the pivot point. |

## Drive State

The following table provides an overview of the drive state variables available in AMCore. These variables allow you to request, monitor, and diagnose drive state transitions. You only need to set the **command drive state** and check the **actual drive state** - all other variables are primarily for diagnostics and troubleshooting.

| **Name** | **Access** | **Units** | **Description** |
| --- | --- | --- | --- |
| G\_DD\_DRIVE\_STATE\_COMMAND\<x><br>**Scope:** CNC<br>**Type:** Integer | Read-Write | \-  | Requests a transition to a specific drive state where `<x>` is a logical device number.<br><br>kIdle = 0<br>kPowerOn = 1<br>kPowerTorqueOn = 2<br>kQuickStop = 3<br>kFaultReset = 4<br><br>&#8505; If you are using the core logic, you do not need to interact with this variable. |
| G\_DD\_DRIVE\_STATE\_ACTUAL\<x><br>**Scope:** CNC<br>**Type:** Integer | Read-Only | \-  | Indicates the current drive state where `<x>` is a logical device number.<br><br>kInvalid = 0<br>kDisabled = 1<br>kPowerOnInProgress = 2<br>kPoweredOn = 3<br>kPowerTorqueOnInProgress = 4<br>kPoweredTorqueOn = 5<br>kQuickStopInProgress = 6<br>kQuickStopActive = 7<br>kFaultActive = 8<br>kFaultResetInProgress = 9<br>kFaultResetComplete = 10<br><br>&#8505; If you are using the core logic, you do not need to interact with this variable. |
| G\_DD\_DRIVE\_STATE\_PERIOD\<x><br>**Scope:** CNC<br>**Type:** Integer | Read-Only | Servo update period count | Tracks how long the drive remains in a specific drive state where `<x>` is a logical device number.<br><br>&#8505; If you are using the core logic, you do not need to interact with this variable. |
| G\_DD\_READY\_TO\_OPERATE\<x><br>**Scope:** CNC<br>**Type:** Integer | Read-Only | \-  | Indicates whether the drive is fully prepared for operation where `<x>` is a logical device number.<br><br>NO_POWERUP = 0<br>READY_FOR_POWERUP = 1<br>POWER_SUPPLY_READY = 2<br>DRIVE_READY = 3<br><br>&#8505; If you are using the core logic, you do not need to interact with this variable. |
| G\_DD\_COE\_DRIVE\_STATE\_COMMANDED\<x><br>**Scope:** CNC<br>**Type:** Integer | Read-Only | \-  | Reflects the commanded drive state based on the **DS402** standard where `<x>` is a logical device number.<br><br>kIdle = 0<br>kShutdown = 1<br>kSwitchOn = 2<br>kDisableVoltage = 3<br>kQuickStop = 4<br>kDisableOperation = 5<br>kEnableOperation = 6<br>kFaultReset = 7<br><br>&#8505; If you are using the core logic, you do not need to interact with this variable. |
| G\_DD\_COE\_DRIVE\_STATE\_ACTUAL\<x><br>**Scope:** CNC<br>**Type:** Integer | Read-Only | \-  | Reflects the actual drive state according to the **DS402** standard where `<x>` is a logical device number.<br><br>kNotReadyToSwitchOn = 0<br>kSwitchOnDisabled = 1<br>kReadyToSwitchOn = 2<br>kSwitchedOn = 3<br>kOperationEnabled = 4<br>kQuickStopActive = 5<br>kFaultReactionActive = 6<br>kFault = 7<br><br>&#8505; If you are using the core logic, you do not need to interact with this variable. |

## Cyclic Data Access

The following table provides an overview of the variables used for accessing cyclic process data input and output. These variables allow you to retrieve and interact with object entries in the **Process Data Input (PDI)** and **Process Data Output (PDO)**. The format of each value depends on the object's data type and display format.

| **Name** | **Access** | **Units** | **Description** |
| --- | --- | --- | --- |
| (DD\<x>)PDOUT\_DATA\<y><br>**Scope:** DD<br>**Type:** Integer | Read | \-  | Retrieves the value of an object entry in the **Process Data Output** for logical device `x`, where `y` specifies the Process Data Output index for the device. |
| (DD\<x>)PDOUT\_NAME\<y><br>**Scope:** DD<br>**Type:** String | Read | \-  | Retrieves the name of an object entry in the **Process Data Output** for logical device `x`, where `y` specifies the Process Data Output index for the device. |
| (DD\<x>)PDOUT\_ID\<y><br>**Scope:** DD<br>**Type:** String | Read | Index:SubIndex | Retrieves the object index and entry sub-index identifying an object entry in the **Process Data Output** for logical device `x`, where `y` specifies the Process Data Output index for the device. |
| (DD\<x>)PDOUT\_TYPE\<y><br>**Scope:** DD<br>**Type:** String | Read | \-  | Retrieves the data type of an object entry in the **Process Data Output** for logical device `x`, where `y` specifies the Process Data Output index for the device. |
| (DD\<x>)PDIN\_DATA\<y><br>**Scope:** DD<br>**Type:** Integer | Read | \-  | Retrieves the value of an object entry in the **Process Data Input** for logical device `x`, where `y` specifies the Process Data Input index for the device. |
| (DD\<x>)PDIN\_NAME\<y><br>**Scope:** DD<br>**Type:** String | Read | \-  | Retrieves the name of an object entry in the **Process Data Input** for logical device `x`, where `y` specifies the Process Data Input index for the device. |
| (DD\<x>)PDIN\_ID\<y><br>**Scope:** DD<br>**Type:** String | Read | Index:SubIndex | Retrieves the object index and entry sub-index identifying an object entry in the **Process Data Input** for logical device `x`, where `y` specifies the Process Data Input index for the device. |
| (DD\<x>)PDIN\_TYPE\<y><br>**Scope:** DD<br>**Type:** String | Read | \-  | Retrieves the data type of an object entry in the **Process Data Input** for logical device `x`, where `y` specifies the Process Data Input index for the device. |

## System health

Each CNC model supports a subset of the variables listed below, since different motherboards provide different system health data. The remaining variables will not be updated.

None of these variables will be updated if you are running AMCore as a simulator.

| Name | Access | Units | Description |
| --- | --- | --- | --- |
| G\_SYSMON\_TEMP\_CPU<br>**Scope:** CNC<br>**Type:** Float | Read-Only | &deg;C  | Temperature of the CPU.<br><br>Measured by a designated CPU temperature sensor on the motherboard. |
| G\_SYSMON\_TEMP\_SYS<br>**Scope:** CNC<br>**Type:** Float | Read-Only | &deg;C  | Temperature of the main system. |
| G\_SYSMON\_TEMP\_AUX<br>**Scope:** CNC<br>**Type:** Float | Read-Only | &deg;C  | Temperature of the auxiliary system. |
| G\_SYSMON\_TEMP\_HDD<br>**Scope:** CNC<br>**Type:** Float | Read-Only | &deg;C  | Temperature of the hard disk. |
| G\_SYSMON\_TEMP\_CPU\_ZERO<br>**Scope:** CNC<br>**Type:** Float | Read-Only | &deg;C  | Temperature of core 0 of the CPU.<br><br>Only updated for CPUs that measure their core temperatures. |
| G\_SYSMON\_TEMP\_CPU\_ONE<br>**Scope:** CNC<br>**Type:** Float | Read-Only | &deg;C  | Temperature of core 1 of the CPU.<br><br>Only updated for CPUs that measure their core temperatures. |
| G\_SYSMON\_TEMP\_CPU\_TWO<br>**Scope:** CNC<br>**Type:** Float | Read-Only | &deg;C  | Temperature of core 2 of the CPU.<br><br>Only updated for CPUs that measure their core temperatures. |
| G\_SYSMON\_TEMP\_CPU\_THREE<br>**Scope:** CNC<br>**Type:** Float | Read-Only | &deg;C  | Temperature of core 3 of the CPU.<br><br>Only updated for CPUs that measure their core temperatures. |
| G\_SYSMON\_TEMP\_CPU\_FOUR<br>**Scope:** CNC<br>**Type:** Float | Read-Only | &deg;C  | Temperature of core 4 of the CPU.<br><br>Only updated for CPUs that measure their core temperatures. |
| G\_SYSMON\_TEMP\_CPU\_FIVE<br>**Scope:** CNC<br>**Type:** Float | Read-Only | &deg;C  | Temperature of core 5 of the CPU.<br><br>Only updated for CPUs that measure their core temperatures. |
| G\_SYSMON\_FAN\_RPM\_CPU<br>**Scope:** CNC<br>**Type:** Float | Read-Only | RPM | Fan speed of the CPU. |
| G\_SYSMON\_FAN\_RPM\_SYS<br>**Scope:** CNC<br>**Type:** Float | Read-Only | RPM | Speed of the system fan.<br><br>Only updated when a system fan is present. |
| G\_SYSMON\_FAN\_RPM\_AUX<br>**Scope:** CNC<br>**Type:** Float | Read-Only | RPM | Speed of the auxiliary fan.<br><br>Only updated when a auxiliary fan is present. |
| G\_SYSMON\_VOLT\_CPU\_VCORE<br>**Scope:** CNC<br>**Type:** Float | Read-Only | mV  | Core voltage of the CPU. |
| G\_SYSMON\_VOLT\_TWELVE\_V\_RAIL<br>**Scope:** CNC<br>**Type:** Float | Read-Only | mV  | Voltage of the 12V rail.<br><br>Commell and DFI motherboards only. |
| G\_SYSMON\_VOLT\_ANLG\_THREE\_THREE\_V<br>**Scope:** CNC<br>**Type:** Float | Read-Only | mV  | Voltage of the 3.3V analog source of the motherboard. |
| G\_SYSMON\_VOLT\_DIG\_THREE\_THREE\_V<br>**Scope:** CNC<br>**Type:** Float | Read-Only | mV  | Commell motherboards only. |
| G\_SYSMON\_VOLT\_FIVE\_V\_RAIL<br>**Scope:** CNC<br>**Type:** Float | Read-Only | mV  | Voltage of the 5V rail. |
| G\_SYSMON\_VOLT\_UNKNOWN<br>**Scope:** CNC<br>**Type:** Float | Read-Only | mV  | Commell motherboards only. |
| G\_SYSMON\_VOLT\_THREE\_THREE\_V\_RAIL<br>**Scope:** CNC<br>**Type:** Float | Read-Only | mV  | Commell motherboards only. |
| G\_SYSMON\_VOLT\_THREE\_THREE\_V\_STDBY<br>**Scope:** CNC<br>**Type:** Float | Read-Only | mV  | Voltage of the 3.3V standby voltage.<br><br>Commell and DFI motherboards only. |
| G\_SYSMON\_VOLT\_THREE\_V\_BATTERY<br>**Scope:** CNC<br>**Type:** Float | Read-Only | mV  | Voltage of the 3V CMOS battery. |
| G\_SYSMON\_HDD\_USED<br>**Scope:** CNC<br>**Type:** Float | Read-Only | %   | Percentage of hard disk space used. |
| G\_SYSMON\_RAM\_MEM<br>**Scope:** CNC<br>**Type:** Float | Read-Only | %   | Percentage of total RAM used. |
| G\_SYSMON\_RAM\_USED<br>**Scope:** CNC<br>**Type:** Integer | Read-Only | GB  | Amount of RAM used. |
| G\_SYSMON\_RAM\_AVAILABLE<br>**Scope:** CNC<br>**Type:** Integer | Read-Only | GB  | Amount of RAM available (unused). |
| G\_SYSMON\_CPU\_LOAD<br>**Scope:** CNC<br>**Type:** Float | Read-Only | %   | Percentage of total CPU utilization. |
| G\_SYSMON\_CPU\_LOAD\_ZERO<br>**Scope:** CNC<br>**Type:** Float | Read-Only | %   | Percentage of CPU core 0 utilization. |
| G\_SYSMON\_CPU\_LOAD\_ONE<br>**Scope:** CNC<br>**Type:** Float | Read-Only | %   | Percentage of CPU core 1 utilization. |
| G\_SYSMON\_CPU\_LOAD\_TWO<br>**Scope:** CNC<br>**Type:** Float | Read-Only | %   | Percentage of CPU core 2 utilization. |
| G\_SYSMON\_CPU\_LOAD\_THREE<br>**Scope:** CNC<br>**Type:** Float | Read-Only | %   | Percentage of CPU core 3 utilization. |
| G\_SYSMON\_CPU\_LOAD\_FOUR<br>**Scope:** CNC<br>**Type:** Float | Read-Only | %   | Percentage of CPU core 4 utilization. |
| G\_SYSMON\_CPU\_LOAD\_FIVE<br>**Scope:** CNC<br>**Type:** Float | Read-Only | %   | Percentage of CPU core 5 utilization. |
| G\_SYSMON\_CPU\_BUS\_SPEED<br>**Scope:** CNC<br>**Type:** Float | Read-Only | MHz | Clock speed of the CPU.<br><br>The value is constant. |
| G\_SYSMON\_FAN\_CPU\_PRESENT<br>**Scope:** CNC<br>**Type:** Boolean | Read-Only | \-  | A value indicating whether the CPU fan is present. |
| G\_SYSMON\_FAN\_SYS\_PRESENT<br>**Scope:** CNC<br>**Type:** Boolean | Read-Only | \-  | A value indicating whether the system fan is present. |
| G\_SYSMON\_FAN\_AUX\_PRESENT<br>**Scope:** CNC<br>**Type:** Boolean | Read-Only | \-  | A value indicating whether the auxiliary fan is present. |
| G\_SYSMON\_CPU\_ONE\_PRESENT<br>**Scope:** CNC<br>**Type:** Boolean | Read-Only | \-  | A value indicating whether CPU core 1 is present. |
| G\_SYSMON\_CPU\_TWO\_PRESENT<br>**Scope:** CNC<br>**Type:** Boolean | Read-Only | \-  | A value indicating whether CPU core 2 is present. |
| G\_SYSMON\_CPU\_THREE\_PRESENT<br>**Scope:** CNC<br>**Type:** Boolean | Read-Only | \-  | A value indicating whether CPU core 3 is present. |
| G\_SYSMON\_CPU\_FOUR\_PRESENT<br>**Scope:** CNC<br>**Type:** Boolean | Read-Only | \-  | A value indicating whether CPU core 4 is present. |
| G\_SYSMON\_CPU\_FIVE\_PRESENT<br>**Scope:** CNC<br>**Type:** Boolean | Read-Only | \-  | A value indicating whether CPU core 5 is present. |
| G\_SYSMON\_MONITORING\_ACTIVE<br>**Scope:** CNC<br>**Type:** Boolean | Read-Only | \-  | A value indicating whether the system monitoring is running. |

Note that CPU Core 0 is assumed to always be present, so there is no variable `G_SYSMON_CPU_ZERO_PRESENT`.

## Misc

These variables are used to provide feedback to other parts of the system such as PLC

| Variable | Access | Units | Description |
| --- | --- | --- | --- |
| G\_AXIS\_LABEL\_MAP\<n-1><br>**Scope:** CNC<br>**Type:** String | Read-Only | \-  | Axis label of axis \<n> (1 to 48). |
| G\_ECAM\_SLAVE\_TO\_MASTER\_MAP\<n-1><br>**Scope:** CNC<br>**Type:** Integer | Read-Only | \-  | Electronic CAM master index from a given slave \<n> (1 to 48) |
| G\_BLOCKING\_BARRIER\_ID\<ppp-1><br>**Scope:** PPP<br>**Type:** Integer | Read-Only | \-  | Barrier ID for a specified PPP (1 to 3)<br><br>A barrier ID is a positive number, ID = 0 indicates that PPP is not blocked |