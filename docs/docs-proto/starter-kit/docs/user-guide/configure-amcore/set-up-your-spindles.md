# Set up your spindles

This section provides steps to configure a spindle on top of the pre-configured 4 default spindles.

## Configure a spindle

AMCore supports up to 10 spindles from AMCore 1.6 onwards. The first 4 spindles can be used out-of-the-box as it is configured by default.

In order to use additional spindles, set the following parameters:

- [Spindle speed units mode group name and number](../reference/parameter-reference.md#spindle)
- [Preparatory word for Constant Surface Speed (CSS) and Constant Surface Speed (RPM) modes](../reference/parameter-reference.md#spindle)
- [Preparatory word for feedrate mode](../reference/parameter-reference.md#spindle)

## Configure M-Code

Spindle features are controlled and activated by PLC. The following features are required to be handled by PLC:

- Activate/Deactivate the spindle
- Switching control mode
- Spindle orientation

## Set spindle speed

There are 2 syntaxes to set spindle speed. The first syntax can only be used for spindle 1-4:

```
S or SPINDLE for spindle 1
SS or SPINDLESS for spindle 2
SSS or SPINDLESSS for spindle 3
SSSS or SPINDLESSSS for spindle 4

Zy - where y is a literal of spindle speed
Z(y) - where y is an expression of spindle speed
where Z is any keyword for spindle speed
```

The second syntax applies to all spindles:

```
S(x)y or SPINDLE(x)y where x is the spindle number and y is a literal of spindle speed
S(x)(y) or SPINDLE(x)(y) where x is the spindle number and y is an expression of spindle speed
```

## Set spindle Speed Limit

There are 2 syntaxes to set spindle speed limit. The first syntax can only be used for spindle 1-4:

```
SPINLIMIT for spindle 1
SPINLIMITSS for spindle 2
SPINLIMITSSS for spindle 3
SPINLIMITSSSS for spindle 4

Zy - where y is a literal of spindle speed limit
Z(y) - where y is an expression of spindle speed limit
where Z is any keyword for spindle speed limit
```

The second syntax applies to all spindles:

```
SPINLIMIT (x)y  where x is the spindle number and y is a literal of spindle speed limit
SPINLIMIT (x)(y) where x is the spindle number and y is an expression of spindle speed limit
```