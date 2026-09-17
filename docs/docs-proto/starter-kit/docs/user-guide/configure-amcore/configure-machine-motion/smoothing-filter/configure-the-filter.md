# Configure the filter

## Set smoothing factor

The smoothing factor determines the strength of the smoothing filter. You can use [smoothing\_factor](../../../reference/parameter-reference.md#motion-control) parameter or [G\_SMOOTHING\_FACTOR](../../../reference/variable-reference.md#motion-control) variable to specify the smoothing factor. 

> [!WARNING]
> After changing `G_SMOOTHING_FACTOR` , a `sync` EPPL command is needed to apply the new value.

If you set the smoothing factor to 0, the filter will be disabled. Setting it to higher values results in smoother position commands. The maximum allowed value for smoothing factor is 99. Each logical machine can have a different smoothing factor.

Set the smoothing factor to either zero or an odd integer between 3 and 99 (a smoothing factor of 1 will have no effect). If you specify a non-zero even value, the next odd integer number will be used instead. For example if smoothing factor is set to 4, a value of 5 will be used.

Smoothing filter improves the smoothness of the system by eliminating high frequency content from the command signal that the servo drives have to follow. The bigger the smoothing factor, the greater the improvement in smoothness will be. However, since a bigger smoothing factor causes more deviation from the programmed toolpath, a trade-off has to be made.

### How to determine the best value

In order to select the best value for smoothing factor, you can measure the deviation that a specific smoothing factor introduces (a method for measuring the deviation is explained in [Effects of the filter](effects-of-the-filter.md#effects-of-the-filter) section). Then if the deviation is greater than the acceptable tolerance, decrease the smoothing factor. If the introduced deviation is smaller than the permissible tolerance, increase the smoothing factor. Repeat this procedure until an optimal setting is found.

## Set transitional jerk limit

If smoothing factor is zero, set [transitional jerk limit](../../../reference/parameter-reference.md#motion-limits) to a value equal to [tangential jerk limit](../../../reference/parameter-reference.md#motion-limits). If smoothing factor is non-zero, then use the below formula:

`transitional jerk limit = smoothing factor * tangential jerk limit`

For example if tangential jerk limit is set to 100000 mm/s<sup>3</sup> and smoothing factor is set to 15, transitional jerk limit should be set to 1500000 mm/s<sup>3</sup>.

## Set smoothing type

You can use [smoothing\_type](../../../reference/parameter-reference.md#motion-control) parameter or [G\_SMOOTHING\_TYPE](../../../reference/variable-reference.md#motion-control) variable to specify the smoothing type.

> [!WARNING]
> If `G_SMOOTHING_TYPE` is used to change the smoothing type, a `sync` EPPL command is needed afterwards to apply the change.

Two types of smoothing filters are available. Type 0 is selected when `smoothing_type` or `G_SMOOTHING_TYPE` are set to 0 (this is the default setting). Type 2 is selected when `smoothing_type` or `G_SMOOTHING_TYPE` is set to 2. Types 1 and 3 are deprecated and should not be used.

If you use smoothing type 2, you will have less deviation from the programmed toolpath and also lower frequency content in the filtered signal. However, the peak jerk value can be greater in some situations (for example at line to arc transitions).

Although the default type is 0 (due to historical reasons and backward compatibility), for most applications, type 2 is recommended. Alternatively you can use the below procedure to decide which type to use.

### How to determine the right type

To select between type 0 and type 2 for a logical machine, follow the below procedure.

1. Set smoothing type to 0. Adjust the smoothing factor and transition jerk limit by following the recommended procedures explained earlier.
2. Machine or cut a part and measure the quality.
3. Set smoothing type to 2. Adjust the smoothing factor and transition jerk limit by following the recommended procedures explained earlier.
4. Machine or cut the same part as step 2 and measure the quality.
5. Compare the results from step 2 and step 4 to determine which smoothing type works better for your application.

## Configuration examples

The below example shows an example of a configuration for logical machine 1.

```
*1.smoothing_type: 2
*1.smoothing_factor: 21
*1.jerk: 100000
*1.transition_jerk_limit: 2100000
```

The second example below shows how the configuration can change at runtime using EPPL. A `sync` command is added at the end and prompts the CNC to apply the new values. Also the relationship between jerk (equal to 100000 mm/s3 from the previous example) , smoothing factor and transitional jerk limit has been preserved.

```
G_SMOOTHING_TYPE = 2
G_SMOOTHING_FACTOR = 31
G_TRANSITION_JERK_LIMIT = 3100000
sync
```