# High speed synchronised IO

This feature is introduced as a result of a beam-on-the-fly feature required in Laser project. High Speed Synchronised IO (HSSIO) is a generic solution for turning on/off a digital signal to an EtherCAT drive and shared memory. 

In order to achieve a high level of precision for triggering the digital signal when using HSSIO, the control signals are transmitted with the move command, using an m-code of mode 8. This mode of m-code is always executed **before** the axis move that is in the same block. This means that the m-code must be placed in the first block **after** the axis reaches its target position.

For example, if we want to turn on a laser when the X-axis reaches a target position of 10mm, and turn it off when the X-axis reaches its target of 20mm:

```
N99 X0
N100 X10
N101 X20 BEAMON
N102 X30 BEAMOFF
N104 X40
```

## Configuring an M-code for mode 8

M-codes for controlling HSSIO must be specified as mode 8:

```
*mcode.113.mode: 8
*mcode.114.mode: 8
```

Specify that the output turns on with M113 and turns off with M114:

```
*mcode.113.output_value: 1
*mcode.114.output_value: 0
```

Assigning the HSSIO channel for M113 and M114 to channel 1:

```
*mcode.113.channel : 1
*mcode.114.channel:  1
```

Configure an alias for each m-code, so the alias can be used in EPPL instead of the specifying the m-code number:

```
*mcode.113.Name: BEAMON
*mcode.114.Name: BEAMOFF
```

## Specifying Targets

Various targets must be specified as part of the HSSIO definition, which can define either a device or shared memory variable where data will be stored, or to which the trigger signal will be sent.

The target specified for the action time and/or output state, can be either a device number and CoE object index, or an AMCore shared memory variable index:

| Type             | Form                                                                                                                                         | Examples                                                             |
| ---------------- | -------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| CoE object index | `DDx<Y>.<index><<sub_index>>` <br><br>  &#8505;The index and sub index are concatenated together and specified in hex by prefixing with "0x" | `DD1.0x40A000`<br>`DD3.0x8A0107`<br>`DD9.0xPF0710`<br>`DD6.0x1234F0` |
| Shared memory    | `<sm_type><index>`                                                                                                                           | `OP1700`<br>`OP1999`                                                 |

## Setting up Channel

Channel describes the location of output.

Enables HSSIO channel 1:

```
*hssio.1.enabled : on
```

In the example below, there are separate simulation and non-simulation configurations for the same channel:

* for the simulated configuration, the action time will be written in `OPI800` and output state will be written in `OPI801`
* for the non-simulated configuration, action time will be written in index and sub index of `0x604000` of drive with logical address of 1 and output state will be written to `0x8A0107` of the same drive

```
*hssio.1.action_time_target : DD1.0x604000
*sim*hssio.1.action_time_target : OPI800

*hssio.1.output_state_target : DD1.0x8A0107
*sim*hssio.1.output_state_target : OPI801
```

## Setting up Spatial Pulsing

When spatial pulsing is used, the frequency of the PWM signal controlling the laser will change in proportion to the velocity.

To use spatial pulsing, the mode must be set to 1:

```
# 0 : Fixed duty cycle and frequency
# 1 : Spatial pulsing (frequency changes based on velocity)
*hssio.1.mode : 1
```

### Joints

The calculated PWM frequency is proportional to the combined velocity of all the specified joints:

```
*hssio.1.spatial_pulsing.joints: 1, 2
```
With the above setting, the vector summation of the velocities of the 1st and the 2nd joint will be used for calculating the velocity, for example if the velocity of joint 1 is denoted by v<sub>1</sub> and the velocity of joint 2 is denoted by v<sub>2</sub> then the frequency will be proportional to &radic;(v<sub>1</sub><sup>2</sup> + v<sub>2</sub><sup>2</sup> ).

### Maximum PWM Frequency

The maximum PWM frequency must also be set. Exceeding this frequency will raise an error:

```
*hssio.1.spatial_pulsing.maximum_frequency: 500000
```

### Targets

In the example below, there are separate simulation and non-simulation configurations for the same channel:

* for the simulated configuration, the frequency will be written to `OPI802` and PWM duty cycle will be written to `OPI803`,
* for the non-simulated configuration, the frequency will be written to the drive configured as logical device 2, into CoE object `0x604100` and the PWM duty cycle will be written to CoE object `0x607A00` of the same drive

```
*hssio.1.spatial_pulsing.frequency_target: DD2.0x604100 
*sim*hssio.1.spatial_pulsing.frequency_target: OPI802

*hssio.1.spatial_pulsing.duty_cycle_target: DD2.0x607A00 
*sim*hssio.1.spatial_pulsing.duty_cycle_target: OPI803
```

> [!WARNING]
> `0x6041` and `0x607A` are used only as an example of CoE objects but are not valid objects to use in practice with spatial pulsing when using drives that conform to Cia402.

## Enabling Spatial Pulsing

The below EPPL command can be used to turn spatial pulsing on from a part program. When spatial pulsing is enabled, it will overwrite the outputs controlled by data block mapping.

When enabling spatial pulsing, the distance is specified in millimeters, and the duty cycle is specified as a percentage:

```
SPATIAL_PULSING_START (channel, distance, duty_cycle)
```

In the example below, spatial pulsing for channel 1 is enabled with a pulse occurring every 10 microns, and a duty cycle of 10%:

```
SPATIAL_PULSING_START (1, 0.010, 10)
```

## Disabling Spatial Pulsing 

The below EPPL commands can be used to turn spatial pulsing off for one channel or for all HSSIO channels.

```
SPATIAL_PULSING_END ( channel )
SPATIAL_PULSING_END_ALL ()
```

When spatial pulsing is disabled, normal data block mapping can be used to control the frequency and PWM duty cycle for the laser.

## Frequency Limit Error

When spatial pulsing is enabled, the frequency will increase proportional to the feedrate. If the calculated frequency for channel \<c>, exceeds the limit specified in `hssio.<c>.spatial_pulsing.maximum_frequency` a warning will be displayed. The PLC can be notified about this error through one of the below error flags (which will be reset once spatial pulsing is re-enabled for that channel):
  
* `XOLB_HSSIO_CHANNEL_1_FREQ_EXCEEDED`
* `XOLB_HSSIO_CHANNEL_2_FREQ_EXCEEDED`
* `XOLB_HSSIO_CHANNEL_3_FREQ_EXCEEDED`
* `XOLB_HSSIO_CHANNEL_4_FREQ_EXCEEDED`


## HSSIO Reset

In the sample configuration above, M114 will turn off the HSSIO. However, there are some events within AMCore that will also turn off the HSSIO without waiting for M114. Such events include:

* start of the main program
* end of the main program
* abort
* emergency stop
* pp execution error