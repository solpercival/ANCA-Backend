# Set up a drive

This section is a brief introduction to the configuration required for ANCA Motion drives.

## Change the firmware

You should specify the required firmware version for each drive, to ensure your configuration is appropriate for the version of firmware on the drive.

To do this, for each device:

1. Set the [Firmware version](../../reference/parameter-reference.md#drives) parameter to the version you want to use on that device.
2. Provide a path to the firmware image using the [Firmware root path](../../reference/parameter-reference.md#drives) and [Firmware file](../../reference/parameter-reference.md#drives) parameters.
3. Set the [Bootloader version](../../reference/parameter-reference.md#drives) parameter to the version you want to use on that device.
4. Provide a path to the bootloader image using the [Bootloader root path](../../reference/parameter-reference.md#drives) and [Bootloader file](../../reference/parameter-reference.md#drives) parameters.

## Set drive parameters

Drive parameter configuration will be managed through **ENIBuilder** in a future update. Details on how to configure parameters using ENIBuilder will be provided once implementation is complete.