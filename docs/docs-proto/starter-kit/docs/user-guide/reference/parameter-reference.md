# Parameter reference

Parameters are persistent settings that configure the behaviour of AMCore. This section lists the key parameters used by AMCore.

> [!NOTE]
> See the [Parameters](../concepts.md#parameters) concept for more information on parameters.

## Kinematics

| Name | Key | Description |
| --- | --- | --- |
| Joint logical device | `<j>.device` | Allocates a logical device to joint `<j>` (1 to 48).<br><br>**Class** - `Joint.Device`<br><br>**Type** - Integer |
| Joint logical machine | `<j>.lm_num` | Allocates a logical machine to joint `<j>` (1 to 48).<br><br>**Class** - `Joint`<br><br>**Type** - Integer |
| Logical machine axes | `<lm>.x<i>.lm_map` | Allocates an axis to the `<i>` th (1 to 48) ordinate of logical machine `<lm>` (1 to 3). The value must match an axis label.<br><br>**Class** - `Lm_num.Ord.Lm_map`<br><br>**Type** - String |
| Nominal radius | `<a>.nomrad` | Defines the nominal radius of axis with label `<a>` (possible values [here](../configure-amcore/set-up-your-axes.md#set-up-your-axes)).<br><br>**Class** - `Dim.Nomrad`<br><br>**Type** - Float<br><br>**Units** - mm |
| Kinematics type | `kinematics` | Determines the kinematics type. See [Configure kinematics](../configure-amcore/configure-kinematics/configure-kinematics.md#configure-kinematics) for available options.<br><br>**Class** - `Kinematics`<br><br>**Type** - String<br><br>**Default** - Blank |
| Static effector offsets | `effector.<n>.static_offset.<a>` | Determines the static effector offset along axis `<a>` on end effector `<n>` for bevel head type 1 kinematics.<br><br>**Class** - `Effector.No.Offset.Axis`<br><br>**Type** - Float<br><br>**Default** - 0 |
| Axis label | `<n>.axis_label` | Determines the axis label for axis \<n> (1-48).<br><br>**Class** - `Axis.Axis_label`<br><br>**Type** - Integer<br><br>**Default** - NOT\_USED |
| CyGrindBx incline angle | `cygrindbx_incline_angle` | Determines the incline angle for CyGrindBx kinematics.<br><br>**Class** - `Cygrindbx_Incline_Angle`<br><br>**Type** - Float<br><br>**Default** - 0.0 |
| Bevel head B to C ratio | `bevel_head_BtoC_ratio` | Determines bevel head B to C axis ratio for Bevel head PQR kinematics.<br><br>**Class** - `Bevel_head_BtoC_ratio`<br><br>**Type** - Float<br><br>**Default** - 0.0 |
| Bevel head B to C centre offset | `bevel_head_BtoC_centre_offset` | Determines bevel head B to C axis centre offset for Bevel head PQR kinematics.<br><br>**Class** - `Bevel_head_BtoC_centre_offset`<br><br>**Type** - Float<br><br>**Default** - 0.0 |
| Bevel head frame angle | `bevel_head_frame_angle` | Determines bevel head frame angle for Bevel head PQR kinematics.<br><br>**Class** - `Bevel_head_frame_angle`<br><br>**Type** - Float<br><br>**Default** - 0.0 |
| X slave feature | `feature.xslv_lm<lm>` | Enable X slave feature for logical machine `<lm>` (1 to 3). `Slave Axes` license is required for this feature.<br><br>**Class** - `Feature.Enabled`<br><br>**Type** - Integer |
| Y slave feature | `feature.yslv_lm<lm>` | Enable Y slave feature for logical machine `<lm>` (1 to 3). `Slave Axes` license is required for this feature.<br><br>**Class** - `Feature.Enabled`<br><br>**Type** - Integer |
| A slave feature | `feature.aslv_lm<lm>` | Enable A slave feature for logical machine `<lm>` (1 to 3). `Slave Axes` license is required for this feature.<br><br>**Class** - `Feature.Enabled`<br><br>**Type** - Integer |
| Bevel head kinematics mode | `bevel_head_mode` | Default mode for bevel head kinematics. Can be either 0 or 1. If mode 0 is selected, joint 3 will be controlled by bevel head kinematics (if enabled). In this case, if the head rotates using A or B axis, joint 3 may move as a result. If mode 1 is selected, joint 3 will have a simple one to one mapping with Z axis. In this case, the rotation of A or B axis will have no effect on joint 3 through AMCore. You can change the bevel head mode using `bevel_head_mode` EPPL command. The current mode is indicated by `G_BEVEL_HEAD_MODE` variable.<br><br>**Class** - `Bevel_head_mode`<br><br>**Type** - Integer<br><br>**Default** - 0 |

## EtherCAT

### General

| Name | Key | Description |
| --- | --- | --- |
| Device EtherCAT address | `<d>.ethercat_address` | Allocates an EtherCAT physical address to logical device `<d>` (1 or higher).<br><br>An address of 0 indicates that there is no device present.<br><br>**Class** - `Device.Address`<br><br>**Type** - Integer |
| Device name | `<d>.ds_device_name` | Name of logical device `<d>` (1 or higher).<br><br>The name should indicate the use of the device, i.e. "X-axis".<br><br>**Class** - `Device.Name`<br><br>**Type** - String |
| Device control type | `<d>.control_type` | Defines the control type of logical device `<d>` (1 or higher).<br><br>If the value is one of the specific drive values, the device is interpreted as a drive (of that type). Other values define custom control types, which are interpreted as IO devices.<br><br>**Class** - `Device.Control`<br><br>**Type** - String<br><br>**Default** - `NOT_USED`<br><br>**Drive values** - `position`, `position_rotational`, `position_and_velocity`, `position_spindle`, or `velocity` |
| EtherCAT Network Information file | `ethercat.File` | Specifies the path to the master XML (ENI) file defining the fieldbus devices.<br><br>**Class** - `Ethercat.File`<br><br>**Type** - String |
| Product name | `vendor_<v>.product_<p>.name` | Defines the product name of an EtherCAT slave device. Default values are as appropriate for ANCA Motion devices.<br><br>The vendor ID `<v>` and product ID `<p>` must be defined as integers (not hex codes).<br><br>**Class** \- `Vendor_id.Product_code.Name`<br><br>**Type** - String<br><br>**Default** \- `Unknown device` |

### IO devices

| Name | Key | Description |
| --- | --- | --- |
| Control type description | `<c>.description` | Optionally used to define a list of control type blocks separated by a "`+`" character, allowing device IO for control type `<c>` (defined by device control type) to be unpacked in a non-default order.<br><br>**Class** - `Device.Control`<br><br>**Type** - Integer<br><br>&#8505; This parameter is **obsolete** and should not be used in new configurations. |
| Control type digital input count | `<c>.di` | Number of digital inputs to unpack into shared memory IPB space for control type `<c>` (defined by device control type).<br><br>**Class** - `Type.Attr`<br><br>**Type** - Integer<br><br>**Default** - 0<br><br>&#8505; This parameter is obsolete and should not be used in new configurations. AMCore now utilizes data from the ENI file for configuration. |
| Control type digital output count | `<c>.do` | Number of digital outputs to unpack into shared memory OPB space for control type `<c>` (defined by device control type).<br><br>**Class** - `Type.Attr`<br><br>**Type** - Integer<br><br>**Default** - 0<br><br>&#8505; This parameter is obsolete and should not be used in new configurations. AMCore now utilizes data from the ENI file for configuration. |
| Control type analog input count | `<c>.ai` | Number of analog inputs to unpack into shared memory IPI space for control type `<c>` (defined by device control type).<br><br>**Class** - `Type.Attr`<br><br>**Type** - Integer<br><br>**Default** - 0<br><br>&#8505; This parameter is obsolete and should not be used in new configurations. AMCore now utilizes data from the ENI file for configuration. |
| Control type analog input size | `<c>.<i>.ipi_size` | Number of bytes (1-4) for analog input index `<i>` (starting at 1) in control type `<c>` (defined by device control type).<br><br>**Class** - `Type.Attr`<br><br>**Type** - Integer<br><br>**Default** - 2<br><br>&#8505; This parameter is obsolete and should not be used in new configurations. AMCore now utilizes data from the ENI file for configuration. |
| Control type analog output count | `<c>.ao` | Number of analog outputs to unpack into shared memory OPI space for control type `<c>` (defined by device control type).<br><br>**Class** - `Type.Attr`<br><br>**Type** - Integer<br><br>**Default** - 0<br><br>&#8505; This parameter is obsolete and should not be used in new configurations. AMCore now utilizes data from the ENI file for configuration. |
| Control type analog output size | `<c>.<i>.opi_size` | Number of bytes (1-4) for analog output index `<i>` (starting at 1) in control type `<c>` (defined by device control type).<br><br>**Class** - `Type.Attr`<br><br>**Type** - Integer<br><br>**Default** - 2<br><br>&#8505; This parameter is obsolete and should not be used in new configurations. AMCore now utilizes data from the ENI file for configuration. |
| Control type string input count | `<c>.si` | Number of string inputs to unpack into shared memory IPS space for control type `<c>` (defined by device control type).<br><br>**Class** - `Type.Attr`<br><br>**Type** - Integer<br><br>**Default** - 0<br><br>&#8505; This parameter is obsolete and should not be used in new configurations. AMCore now utilizes data from the ENI file for configuration. |
| Control type string input size | `<c>.<i>.ips_size` | Number of bytes for string input index `<i>` (starting at 1) in control type `<c>` (defined by device control type).<br><br>**Class** - `Type.Attr`<br><br>**Type** - Integer<br><br>&#8505; This parameter is obsolete and should not be used in new configurations. AMCore now utilizes data from the ENI file for configuration. |
| Control type string output count | `<c>.so` | Number of string outputs to unpack into shared memory OPS space for control type `<c>` (defined by device control type).<br><br>**Class** - `Type.Attr`<br><br>**Type** - Integer<br><br>**Default** - 0<br><br>&#8505; This parameter is obsolete and should not be used in new configurations. AMCore now utilizes data from the ENI file for configuration. |
| Control type string output size | `<c>.<i>.ops_size` | Number of bytes for string output index `<i>` (starting at 1) in control type `<c>` (defined by device control type).<br><br>**Class** - `Type.Attr`<br><br>**Type** - Integer<br><br>&#8505; This parameter is obsolete and should not be used in new configurations. AMCore now utilizes data from the ENI file for configuration. |
| Device digital input base address | `<d>.ipb_start` | Starting index of shared memory IPB space for digital inputs for device `<d>` (1 or higher).  The first input is available at the starting index plus 1.<br><br>**Class** - `Device.Attr`<br><br>**Type** - Integer<br><br>**Default** - 0 |
| Device digital output base address | `<d>.opb_start` | Starting index of shared memory OPB space for digital outputs for device `<d>` (1 or higher). The first output is available at the starting index plus 1.<br><br>**Class** - `Device.Attr`<br><br>**Type** - Integer<br><br>**Default** - 0 |
| Device analog input base address | `<d>.ipi_start` | Starting index of shared memory IPI space for analog inputs for device `<d>` (1 or higher). The first input is available at the starting index plus 1.<br><br>**Class** - `Device.Attr`<br><br>**Type** - Integer<br><br>**Default** - 0 |
| Device analog output base address | `<d>.opi_start` | Starting index of shared memory OPI space for analog outputs for device `<d>` (1 or higher). The first output is available at the starting index plus 1.<br><br>**Class** - `Device.Attr`<br><br>**Type** - Integer<br><br>**Default** - 0 |
| Device string input base address | `<d>.ips_start` | Starting index of shared memory IPS space for string inputs for device `<d>` (1 or higher). The first input is available at the starting index plus 1.<br><br>**Class** - `Device.Attr`<br><br>**Type** - String<br><br>**Default** - "" |
| Device string output base address | `<d>.ops_start` | Starting index of shared memory OPS space for string outputs for device `<d>` (1 or higher). The first output is available at the starting index plus 1.<br><br>**Class** - `Device.Attr`<br><br>**Type** - String<br><br>**Default** - "" |
| Device float input base address | `<d>.ipf_start` | Starting index of shared memory IPF space for float inputs for device `<d>` (1 or higher). The first input is available at the starting index plus 1.<br><br>**Class** - `Device.Attr`<br><br>**Type** - Float<br><br>**Default** - 0.0 |
| Device float output base address | `<d>.opf_start` | Starting index of shared memory OPF space for float outputs for device `<d>` (1 or higher). The first output is available at the starting index plus 1.<br><br>**Class** - `Device.Attr`<br><br>**Type** - Float<br><br>**Default** - 0.0 |

### Drives

| Name | Key | Description |
| --- | --- | --- |
| Firmware file | `<d>.Firmware.FileName` | Specifies the path to the firmware image file for device `<d>` (1 or higher), relative to the firmware root path.<br><br>**Class** - `Firmware.FileName`<br><br>**Type** - String |
| Firmware root path | `<d>.Firmware.RootPath` | Specifies the absolute path to the folder that contains firmware images for device `<d>` (1 or higher).<br><br>**Class** - `Firmware.RootPath`<br><br>**Type** - String |
| Firmware version | `<d>.dsd_firmware_version` | The firmware version number required for device `<d>` (1 or higher).<br><br>**Class** - `dsd_firmware_version`<br><br>**Type** - String |
| Bootloader file | `<d>.Bootloader.FileName` | Specifies the path to the bootloader image file for device `<d>` (1 or higher), relative to the bootloader root path. <br><br>**Class** - `Bootloader` `.FileName`<br><br>**Type** - String |
| Bootloader root path | `<d>.Bootloader.RootPath` | Specifies the absolute path to the folder that contains bootloader images for device `<d>` (1 or higher).<br><br>**Class** - `Bootloader` `.RootPath`<br><br>**Type** - String |
| Bootloader version | `<d>.dsd_bootloader_version` | The bootloader version number required for device `<d>` (1 or higher).<br><br>**Class** - `dsd_bootloader_version`<br><br>**Type** - String |

### Probes

> [!WARNING]
> Probing is currently not supported.

| Name | Key | Description |
| --- | --- | --- |
| Probe master | `<p>.probe_master` | Logical address of the master drive for probe `<p>` (1 to 6). The master is the drive that is connected to the relevant probe.<br><br>Set to 0 to disable the probe.<br><br>**Class** - `Probe.Master`<br><br>**Type** - Integer<br><br>**Default** - 0 |
| Probe slave list | `<p>.probe_slaves` | Array of logical addresses of slave drives for probe `<p>` (1 to 6).<br><br>The slaves are the drives that will report their positions, on command from the master, to capture a snapshot of machine position.<br><br>An example configuration, with probe 1 using drives 2 (Y-axis) and 3 (Z-axis) as slaves, is as follows:  <br>`*1.probe_slaves : 2, 3`<br><br>If this parameter is undefined, the deprecated parameter `probe.device_list` (which applies to all probes) will be used instead.<br><br>**Class** - `Probe.Slaves`<br><br>**Type** - Integer Array |
| Probe logical machine | `<p>.probe_lm` | The logical machine to which probe `<p>` (1 to 6) is assigned.<br><br>Other logical machines may not use probe `<p>`.<br><br>**Class** - `Probe.Lm`<br><br>**Type** - Integer<br><br>**Default** - 1 |
| Probe polarity | `probe<p>.polarity` | Default polarity for probe `<p>` (1 to 6).<br><br>Set to `off` for falling-edge probing or `on` for rising-edge probing.<br><br>**Class** - `Probe.Polarity`<br><br>**Type** - Boolean<br><br>**Default** - `off` |
| AT IDN list - probing IDNs | `<d>.ds_at_parameter_list` | Array of Acknowledge Telegram (AT) IDNs for device `<d>` (1 or higher).<br><br>To setup a device as a probe slave, the following IDNs must be added to this list:<br><br>- For rising-edge probing: 130<br>- For falling-edge probing: 131<br><br>To setup a device as a probe master, the following IDNs must be added to this list:<br><br>- 33150<br>- For rising-edge probing: 130, 33151<br>- For falling-edge probing: 131, 33152<br><br>An example configuration for probing is as follows (where `...` represents all other non-probing IDNs):  <br>`*ds_at_parameter_list : ..., 130, 131, 33150, 33151, 33152`<br><br>**Class** - Device.Ds<br><br>**Type** - Integer Array<br><br>**Default** - 51 |

## Motion control

### General

| Name | Key | Description |
| --- | --- | --- |
| Joint position lag error threshold | `<j>.xs_servo_err_tol` | Defines the amount of position lag for joint `<j>` (1 to 48) which, when exceeded, causes an error.<br><br>**Class** - `Joint.Tol`<br><br>**Type** - Float<br><br>**Units** - mm or deg |
| Corner rounding limit | `<lm>.corner_tol` | When transitioning between moves (except splines) on logical machine `<lm>` (1 to 3), the corners may be rounded by an amount less than or equal to this value.<br><br>**Class** - `LM.Fillet`<br><br>**Type** - Float<br><br>**Default** - 0<br><br>**Units** - mm |
| Corner rounding limit for repositioning moves | `<lm>.repos_tol` | Has a similar functionality to `corner_tol` but applies only to corners where one of the moves is a repositioning move. Repositioning moves are only used in laser machines. These are linear or arc moves with the laser beam turn off that are located between two moves with the laser beam turned on.<br><br>**Class** - `LM.Fillet`<br><br>**Type** - Float<br><br>**Default** - 0<br><br>**Units** - mm |
| Smoothing factor | `<lm>.smoothing_factor` | Determines the strength of the joint smoothing filter (a low pass filter that smooths the commanded position) for logical machine `<lm>` (1 to 3). The parameter accepts zero or an odd integer. If a non-zero even number is specified, the next odd number will be used instead.<br><br>**Class** - `LM.Filter`<br><br>**Type** - Integer<br><br>**Default** - 0<br><br>**Range** - 0-99<br><br>**Variable** - [G\_SMOOTHING\_FACTOR](../reference/variable-reference.md#motion-control) |
| Smoothing type | `<lm>.smoothing_type` | Determines the type of the joint smoothing filter (a low pass filter that smooths the commanded position) for logical machine `<lm>` (1 to 3). This parameter can be set to either 0 or 2. When set to 0, a simple low pass filter will be used. When set to 2, a different type of smoothing filter will be enabled that generates lower frequency content and a smaller deviation, but can result in higher jerk values being applied.<br><br>**Class** - `LM.Filter`<br><br>**Type** - Integer<br><br>**Default** - 0<br><br>**Variable** - [G\_SMOOTHING\_TYPE](../reference/variable-reference.md#motion-control) |
| Tangency angle | `<lm>.tangency_angle` | Defines, on logical machine `<lm>` (1 to 3), the angle between successive moves which, when exceeded, causes the machine to pause between the moves.<br><br>**Class** - `LM.Angle`<br><br>**Type** - Float<br><br>**Default** - 15<br><br>**Units** - deg<br><br>**Variable** - [G\_TANGENCY\_ANGLE](../reference/variable-reference.md#motion-control) |
| Dry run velocity | `dry_run_velocity` | Feedrate of the machine when performing a dry run.<br><br>**Class** - `Cnc`<br><br>**Type** - Float<br><br>**Units** - mm/min |
| Pitch compensation folder | `pcomp_folder` | Path of a folder containing pitch compensation data files.<br><br>Must be an absolute path. May contain environment variables.<br><br>Default location (if parameter undefined):  <br>`<home folder>\misc`<br><br>**Class** - `Pcomp`<br><br>**Type** - String |
| Aligning tolerance | `align_tol` | Tolerance for aligning moves. If after aligning the toolpath deviates from the original toolpath more than this value, no aligning will be carried out.<br><br>**Class** - `Cnc`<br><br>**Type** - Float<br><br>**Default** - 0<br><br>**Units** - mm |
| Aligning tolerance for reposition moves | `repos_align_tol` | Tolerance for aligning repositioning moves. This parameter is similar to `align_tol` but is applied to repositioning moves. Repositioning moves are used in laser machines to move the laser head while the laser beam is off.<br><br>**Class** - `Cnc`<br><br>**Type** - Float<br><br>**Default** - 0<br><br>**Units** - mm |
| Aligning buffer size | `align_buffer_size` | The maximum number of moves that can be aligned. Aligning functionality will be disabled if this parameter is set to zero.<br><br>**Class** - `Cnc`<br><br>**Type** - Float<br><br>**Default** - 0<br><br>**Units** - mm |
| Lookahead buffer size | `vel_look_max` | The maximum number of blocks (move or non-move) in the lookahead buffer. The maximum number of move blocks in the lookahead buffer is limited to 100. See [Block lookahead](../configure-amcore/configure-machine-motion/block-lookahead.md#block-lookahead) for more information.<br><br>**Class** - `Vel_look_max`<br><br>**Type** - Integer<br><br>**Default** - 0<br><br>**Range** - 1-200 |

### Scaling

| Name | Key | Description |
| --- | --- | --- |
| Device linear position scaling unit | `<d>.position_scaling_unit` | The linear position scaling unit for device `<d>` (1 to 48). This is the user-defined unit in which positions are sent to and received from the corresponding drive (over the fieldbus).<br><br>AMCore represents positions as floating-point values in mm (or inches), but positions are transmitted to/from the drive as integer multiples of the position scaling unit. This parameter tells AMCore how to convert between the two types of position representations.<br><br>Scientific notation may be used to specify small values in a convenient form.<br><br>Example 1: Setting device 1's linear position scaling unit to 10<sup>-9</sup>m = 1nm, so all positions will be transmitted to/from the corresponding drive as integer multiples of 1nm:<br><br>`*1.position_scaling_unit : 0.000000001`<br><br>Example 2: Setting device 2's linear position scaling unit to 10<sup>-6</sup> inches:<br><br>`*2.position_scaling_unit : 2.54e-8`<br><br>**Class** - `Device.Position_scaling_unit`<br><br>**Type** - Float<br><br>**Default** - 10<sup>-7</sup> (i.e. 10<sup>-7</sup>m = 10<sup>-4</sup>mm)<br><br>**Units** - m |
| Device rotary position scaling unit | `<d>.rotary_scaling_unit` | The rotary position scaling unit for device `<d>` (1 to 48). This is the user-defined unit in which rotary positions are sent to and received from the corresponding drive (over the fieldbus).<br><br>AMCore represents rotary positions as floating-point values in degrees, but positions are transmitted to/from the drive as integer multiples of the rotary scaling unit. This parameter tells AMCore how to convert between the two types of position representations.<br><br>Scientific notation may be used to specify small values in a convenient form.<br><br>Example: Setting device 1's rotary scaling unit to 10<sup>-4</sup> degrees:<br><br>`*1.rotary_scaling_unit : 0.0001`<br><br>**Class** - `Device.Rotary_scaling_unit`<br><br>**Type** - Float<br><br>**Default** - 10<sup>-4</sup> (i.e. 10<sup>-4</sup> degrees)<br><br>**Units** - degrees |
| Device velocity scaling unit | `<d>.velocity_scaling_unit` | The velocity scaling unit for device `<d>` (1 to 48). This is the user-defined unit in which velocities are sent to and received from the corresponding drive (over the fieldbus).<br><br>AMCore represents velocities as floating-point values in RPM, but velocities are transmitted to/from the drive as integer multiples of the velocity scaling unit. This parameter tells AMCore how to convert between the two types of velocity representations.<br><br>Scientific notation may be used to specify small values in a convenient form.<br><br>Example 1: Setting device 1's velocity scaling unit to 10<sup>-4</sup> RPM, so all velocities will be transmitted to/from the corresponding drive as integer multiples of 10<sup>-4</sup> RPM:<br><br>`*1.velocity_scaling_unit : 0.0001`<br><br>Example 2: Setting device 2's velocity scaling unit to 10<sup>-6</sup> RPM:<br><br>`*2.velocity_scaling_unit : 1e-6`<br><br>**Class** - `Device.Velocity_scaling_unit`<br><br>**Type** - Float<br><br>**Default** - 10<sup>-4</sup><br><br>**Units** - RPM |

### Joint limits

| Name | Key | Description |
| --- | --- | --- |
| Joint soft limits active | `<j>.soft_limit_used` | Defines whether or not the soft limits are active for joint `<j>` (1 to 48).<br><br>**Class** -  `Joint.Soft_limit_used`<br><br>**Type** - Boolean<br><br>**Default** - `on` |
| Joint soft limits deceleration | `<j>.soft_limit_max_decel` | Deceleration of joint `<j>` (1 to 48) when approaching a soft limit.<br><br>**Class** - `Joint.Decel`<br><br>**Type** - Float<br><br>**Default** - 1000<br><br>**Units** - mm/s2 or deg/s2 |
| Joint lower soft limit | `<j>.soft_limit_minus` | Minimum position of joint `<j>` (1 to 48).<br><br>**Class** - `Joint.Limit`<br><br>**Type** - Float<br><br>**Units** - mm or deg<br><br>**Variable** [G\_SERVO\_SLM\<j-1>](../reference/variable-reference.md#motion-control) |
| Joint upper soft limit | `<j>.soft_limit_plus` | Maximum position of joint `<j>` (1 to 48).<br><br>**Class** - `Joint.Limit`<br><br>**Type** - Float<br><br>**Units** - mm or deg<br><br>**Variable** [G\_SERVO\_SLP\<j-1>](../reference/variable-reference.md#motion-control) |
| Joint velocity limit | `<j>.max_velocity` | Maximum velocity of joint `<j>` (1 to 48).<br><br>**Class** - `Joint.Velocity`<br><br>**Type** - Float<br><br>**Default** - 2000<br><br>**Units** - mm/min or deg/min |
| Joint rapid-limit velocity limit | `<j>.safe_velocity` | Maximum velocity of joint `<j>` (1 to 48) when the rapid-limit is active.<br><br>**Class** - `Joint.SafeVel`<br><br>**Type** - Float<br><br>**Default** - 1960 (except joint 4 - 17640 and joint 5 - 186.2)<br><br>**Units** - mm/min or deg/min |
| Joint acceleration limit | `<j>.max_accel` | Maximum acceleration of joint `<j>` (1 to 48).<br><br>**Class** - `Joint.Accel`<br><br>**Type** - Float<br><br>**Default** - 600<br><br>**Units** - mm/s2 or deg/s2 |
| Joint deceleration limit | `<j>.max_decel` | Maximum deceleration of joint `<j>` (1 to 48).<br><br>**Class** - `Joint.Decel`<br><br>**Type** - Float<br><br>**Units** - mm/s2 or deg/s2 |
| Joint jerk limit | `<j>.max_jerk` | Maximum jerk of joint `<j>` (1 to 48).<br><br>**Class** - `Joint.Jerk`<br><br>**Type** - Float<br><br>**Default** - 100000<br><br>**Units** - mm/s3 or deg/s3 |

### Motion limits

| Name | Key | Description |
| --- | --- | --- |
| Velocity limit | `contour_rapid_velocity` | Maximum feedrate of the machine. Doesn't affect rapid moves.<br><br>**Class** - `Cnc`<br><br>**Type** - Float<br><br>**Default** - 10000<br><br>**Units** - mm/min |
| Rapid-limit velocity limit | `contour_rapid_limit_velocity` | If neither ILB\_RAPID\_LIMIT, nor ILB\_RAPID\_LIMIT\_2 are set, this parameter has not effect. If ILB\_RAPID\_LIMIT is set, the smaller value between this parameter and 2000 mm/min will be applied to the machine. If ILB\_RAPID\_LIMIT is not set and ILB\_RAPID\_LIMIT\_2 is set, this parameter determines the maximum feedrate of the machine. This parameter applies to rapid and non-rapid moves.<br><br>**Class** - `Cnc`<br><br>**Type** - Float<br><br>**Default** - 2000<br><br>**Units** - mm/min |
| Tangential acceleration limit | `<lm>.acceleration` | Maximum acceleration of logical machine `<lm>` (1 to 3) in the direction it is moving. Doesn't affect rapid moves.<br><br>**Class** - Lm.Accel<br><br>**Type** - Float<br><br>**Default** - 600<br><br>**Units** - mm/s2<br><br>**Variable** [G\_ACCEL](../reference/variable-reference.md#motion-control) |
| Tangential deceleration limit | `<lm>.deceleration` | Maximum deceleration of the end effector of logical machine `<lm>` (1 to 3) in the direction it is moving. Doesn't affect rapid moves.<br><br>**Class** - `Lm.Decel`<br><br>**Type** - Float<br><br>**Default** - 600<br><br>**Units** - mm/s2<br><br>**Variable** [G\_DECEL](../reference/variable-reference.md#motion-control) |
| Radial acceleration limit | `<lm>.radial_acceleration_limit` | Maximum acceleration of the end effector of logical machine `<lm>` (1 to 3) in the direction perpendicular to it's movement. Doesn't affect rapid moves.<br><br>**Class** - `Lm.Accel`<br><br>**Type** - Float<br><br>**Default** - 750<br><br>**Units** - mm/s2<br><br>**Variables** - [G\_RADIAL\_ACCEL\_LIMIT](../reference/variable-reference.md), [G\_RADIAL\_ACCEL\_ORIDE](../reference/variable-reference.md#motion-control) |
| Tangential jerk limit | `<lm>.jerk` | Maximum jerk of the end effector of logical machine `<lm>` (1 to 3) in the direction it is moving. Doesn't affect rapid moves.<br><br>**Class** - `Lm.Jerk`<br><br>**Type** - Float<br><br>**Default** - 100000<br><br>**Units** - mm/s3<br><br>**Variables** [G\_JERK](../reference/variable-reference.md), [G\_JERK\_ORIDE](../reference/variable-reference.md) |
| Radial jerk limit | `<lm>.radial_jerk_limit` | Maximum jerk of the end effector of logical machine `<lm>` (1 to 3) in the direction perpendicular to it's movement. Doesn't affect rapid moves.<br><br>**Class** - `Lm.Jerk`<br><br>**Type** - Float<br><br>**Default** - 100000<br><br>**Units** - mm/s3<br><br>**Variables** [G\_RADIAL\_JERK\_LIMIT](../reference/variable-reference.md), [G\_RADIAL\_JERK\_ORIDE](../reference/variable-reference.md#motion-control) |
| Transitional jerk limit | `<lm>.transition_jerk_limit` | Maximum jerk of the end effector of logical machine `<lm>` (1 to 3) during the transition from one move to the next move. Does not affect rapid moves.<br><br>**Class** - `Lm.Jerk`<br><br>**Type** - Float<br><br>**Default** - 200000<br><br>**Units** - mm/s3<br><br>**Variables** [G\_TRANSITION\_JERK\_LIMIT](../reference/variable-reference.md#motion-control), [G\_TRANSITION\_JERK\_ORIDE](../reference/variable-reference.md#motion-control) |

### MPG

| Name | Key | Description |
| --- | --- | --- |
| MPG velocity limit | `<m>.mpg_velocity_limit` | Maximum feedrate that MPG `<m>` (1 to 12) can generate. If no value is specified, the velocity limit of the end effector is used.<br><br>**Class** - `MPG_Velocity_Limit`<br><br>**Type** - Float<br><br>**Units** - mm or deg |
| MPG gain | `<m>.mpg_gain` | The feedrate of moves of MPG `<m>` (1 to 12) is determined by multiplying the position lag by this parameter and adding the bias.<br><br>**Class** - `Mpg.Gain`<br><br>**Type** - Float<br><br>**Default** - 0.13<br><br>**Units** - MUP\-1 |
| MPG bias | `<m>.mpg_bias` | The feedrate of moves of MPG `<m>` (1 to 12) is determined by adding this parameter to the gain multiplied by the position lag.<br><br>**Class** - `Mpg.Bias`<br><br>**Type** - Float<br><br>**Default** - 2<br><br>**Units** - mm/min |
| MPG position lag limit | `<m>.mpg_max_lag` | Maximum position lag for MPG `<m>` (1 to 12). Pulses that cause this limit to be exceeded are discarded.<br><br>For moves that involve rotary joints, the nominal radius is used. If the move is a single rotary joint, the units are degrees.<br><br>**Class** - `Mpg.Lag`<br><br>**Type** - Float<br><br>**Default** - 3<br><br>**Units** - mm or deg |
| MPG axis position lag limit | `<a>.mpg_max_lag_for_axis` | This parameter is the same as the MPG position lag limit, except it is applied to the axis `<a>` (possible values [here](../configure-amcore/set-up-your-axes.md#set-up-your-axes)) instead of an MPG.<br><br>For moves that involve rotary joints, the nominal radius is used. If the move is a single rotary joint, the units are degrees.<br><br>**Class** - `Mpg.Lag`<br><br>**Type** - Float<br><br>**Default** - 0<br><br>**Units** - mm or deg |
| MPG input window | `<m>.mpg_input_window` | The input for MPG `<m>` (1 to 12) is averaged over time before commanding the axes. This parameter defines the time period over which the input is averaged.<br><br>Smaller values feel more responsive, higher values feel smoother.<br><br>**Class** - `Mpg.Window`<br><br>**Type** - Float<br><br>**Default** - 50<br><br>**Units** - ms |
| MPG live offset input window | `<m>.lo_mpg_input_window` | This parameter is almost the same as the input window, except it only applies to live offset commands and has slightly different units.<br><br>**Class** - `Mpg.Window`<br><br>**Type** - Float<br><br>**Default** - 3<br><br>**Units** - MUP |

## Spindle

| Name | Key | Description |
| --- | --- | --- |
| Spindle speed units mode group name | `spindle.<n>.css_group_name` | Name of spindle speed units mode group for spindle `<n>` (5 to 10).<br><br>**Class** - `Spindle.SpindleNumber.CSSGroupName`<br><br>**Type** - String |
| Spindle speed units mode group number | `spindle.<n>.css_group_number` | Group number of spindle speed units mode for spindle `<n>` (5 to 10).<br><br>**Class** - `Spindle.SpindleNumber.CSSGroupNumber`<br><br>**Type** - Integer |
| Preparatory word to enable Constant Surface Speed (CSS) Mode | `spindle.<n>.css_gcode.on` | Define preparatory word to enable CSS mode for spindle \<n> (5, 10).<br><br>**Class** - `Spindle.SpindleNumber.CSSGCode.Mode`<br><br>**Type** - boolean |
| Preparatory word to disable Constant Surface Speed (CSS) Mode (RPM mode) | `spindle.<n>.css_gcode.off` | Define preparatory word to disable CSS mode for spindle \<n> (5, 10).<br><br>**Class** - `Spindle.SpindleNumber.CSSGCode.Mode`<br><br>**Type** - boolean |
| Default Constant Surface Speed mode | `spindle.<n>.css_mode.<p>.default` | This parameter define the default CSS mode when AMCore starts for spindle \<n> (5, 10) for a PPP \<p>.<br><br>**Class** - `Spindle.SpindleNumber.CSSMode.PPP.Default`<br><br>**Type** - Integer |
| Preparatory word for feedrate mode | `spindle.<n>.feedrate_units_gcode` | This parameter define preparatory word for feedrate mode for spindle \<n> (5, 10).<br><br>**Class** - `Spindle.SpindleNumber.FeedrateUnitsGCode`<br><br>**Type** - Integer |

## PLC

| Name | Key | Description |
| --- | --- | --- |
| PLC name (high-priority) | `<slot>.plc_high` | Name of PLC in high-priority slot `<slot>` (1 to 5).<br><br>Set to `NO_PLC` to leave the slot unused.<br><br>**Class** - `Slot.Pri`<br><br>**Type** - String |
| PLC name (low priority) | `<slot>.plc_low` | Name of PLC in low-priority slot `<slot>` (1 to 5).<br><br>Set to `NO_PLC` to leave the slot unused.<br><br>**Class** - `Slot.Pri`<br><br>**Type** - String |
| PLC source folder | `plc.<name>.srcdir` | Source folder for PLC `<name>` (defined by above 2 parameters).<br><br>This folder contains the PLC configuration file `<name>.db`, which lists the PLC's header files (`*.plh`) and source files (`*.plc`).<br><br>**Class** - `Plc.Name.Dir`<br><br>**Type** - String |

## Tools

| Name | Key | Description |
| --- | --- | --- |
| Params configuration file | `params_file` | Path of the Params tool's configuration file, which contains a list of parameters to display.<br><br>Must be an absolute path. May contain environment variables.<br><br>**Class** - `Params`<br><br>**Type** - String<br><br>**Default** - `<home folder>\db\config\param.db` |
| Watch list folder | `var.dir` | Path of the Watch Variables (var) tool's watch list folder, which is the default location for watch list (`*.lst`) files. This  is the initial folder for the "File &rarr; Load Watch List" and "File &rarr; Save Watch List As" dialog boxes.<br><br>May be an absolute path or relative to `<OemPATH>`. Cannot contain environment variables.<br><br>**Class** - `Dir.dir`<br><br>**Type** - String<br><br>**Default** - `<OemPATH>\var`  (if folder exists, else `%AMCORE_DATA%\var`) |
| Plot default folder | `plt.dir` | Path of the Plot tool's default folder, which is the default location from which data log (`*.dat`) files are loaded. This  is the initial folder for the "File &rarr; Open" dialog box (when AMCore is running).<br><br>May be an absolute path or relative to `<OemPATH>`. Cannot contain environment variables.<br><br>**Class** - `plt.dir`<br><br>**Type** - String<br><br>**Default** - `<OemPATH>\plot` (if folder exists, else `%AMCORE_DATA%\plot`) |
| Data Logger configuration folder | `dl.dir` | Path of the Data Logger tool's configuration folder, which is the default location for configuration (`*.dlcfg`) files. This is the  initial folder for the "File &rarr; Load" and "File &rarr; Save As" dialog boxes, and the default folder for the "File &rarr; Save" function.<br><br>May be an absolute path or relative to `<OemPATH>`. Cannot contain environment variables.<br><br>**Class** - `Dir` `.dir`<br><br>**Type** - String<br><br>**Default** - `<OemPATH>\dl` (if folder exists, else `%AMCORE_DATA%\dl`) |
| Data Logger output folder | `dl.output.dir` | Path of the Data Logger tool's output folder, which is the default folder to which data log (`*.dat`) files are saved.<br><br>May be an absolute path or relative to `<OemPATH>`. Cannot contain environment variables.<br><br>**Class** - `Dir` `.out.dir`<br><br>**Type** - String<br><br>**Default** - `%AMCORE_DATA%\<randomly-generated subfolder>` |

## Pseudo moves

| Name | Key | Description |
| --- | --- | --- |
| Pseudo move error tolerance | `<a>.pseudo_move_error_tol` | Tolerance for pseudo moves for axis `<a>`. If the difference between the position of the axis immediately before `pseudoon` command and the position of the axis immediately before `pseudooff` command exceeds this tolerance, an error will be raised.<br><br>**Class** - `Dim.Pseudo_move`<br><br>**Type** - Float<br><br>**Default** - 0.0005 |

## Compatibility

| Name | Key | Description |
| --- | --- | --- |
| Ignore probe errors | `ignore_probe_errors.compatibility_mode` | Disables probe-related warnings and errors on simulators.<br><br>These warnings and errors cannot be disabled on real hardware.<br><br>**Class** - `Disable_Fixes.Compatibility_Mode`<br><br>**Type** - Boolean<br><br>**Default** - Depends on your AMCore release |
| Limit the number of available axes to 20 | `48axis.compatibility_mode` | Limit the number of axes to 20 for backward compatibility. If the value is On, AMCore will disable 48 axis support mode i.e. limit the number of axes to 20.<br><br>**Class** - `Disable_Fixes.Compatibility_Mode`<br><br>**Type** - Boolean<br><br>**Default** - Depends on your AMCore release |