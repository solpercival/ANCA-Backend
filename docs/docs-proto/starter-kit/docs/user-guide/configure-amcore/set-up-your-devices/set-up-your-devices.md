# Set up your devices

This section provides instructions to enable AMCore to communicate with and understand your EtherCAT devices.

## Background of ESI and ENI Files

The **EtherCAT Slave Information (ESI)** file and the **EtherCAT Network Information (ENI)** file are essential for defining the configuration of devices within an EtherCAT network. These files describe the capabilities of the EtherCAT slaves and the network layout, respectively.

- **ESI File**: The ESI file is an XML-based configuration file that contains information about EtherCAT slaves, including device profiles, supported I/O data, and the capabilities of each slave device. The ESI file provides the necessary details for configuring EtherCAT slaves to communicate with the master system, including the input and output data objects, the cyclic data map, and more.
- **ENI File**: The ENI file is used for network-wide configuration. It provides information about the topology and settings of the EtherCAT network, including device assignments, synchronization, and other communication parameters.

## Define your EtherCAT topology

Provide the path to your EtherCAT Network Information (ENI) file using the [EtherCAT Network Information file](../../reference/parameter-reference.md#ethercat) parameter.

The contents of the ENI file must match the device configuration.

> [!TIP]
> If you need help generating an ENI file, contact your ANCA Motion representative.

Once you've done this, you should be able to restart AMCore and establish device communication.

## Define logical devices

A logical device is an ordered virtual device that can be linked to a physical device. The order of logical devices is independent from the order of physical devices.

In AMCore, you only configure logical devices. This means you can connect the physical devices in any order (i.e. to minimize cables) or modify the physical devices in your system without changing parameters that depend on devices.

It is up to you how to order your logical devices. You should define a logical device for each physical axis of your machine.

To define a logical device:

1. Set the [Device EtherCAT address](../../reference/parameter-reference.md#ethercat) parameter to the corresponding physical address. The physical address of a device is the index (starting at 1) of the device in the EtherCAT topology. 
2. Set an appropriate name by setting the [Device name](../../reference/parameter-reference.md#ethercat) parameter. The name should describe the use of the device rather than the name of the product. For example, name a device "X-axis" rather than "AMD5x Drive". See the [Set up your axes](..//set-up-your-axes.md#set-up-your-axes) page to help determine the axis label you might use for the device.
3. Set it's control type using the [Device control type](../../reference/parameter-reference.md#ethercat) parameter. A custom control type signifies that the device is an IO device. See [Set up an IO device](./set-up-an-io-device.md#set-up-an-io-device) for more information.
4. *(Optional)* For a third party device, provide the product name by setting the [Product name](../../reference/parameter-reference.md#ethercat) parameter. This will greatly improve the usefulness of many diagnostic error messages.

> [!NOTE]
> In other sections, the term device means logical device.