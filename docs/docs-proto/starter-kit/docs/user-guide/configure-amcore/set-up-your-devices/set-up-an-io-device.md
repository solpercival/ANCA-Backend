# Set up an IO device

The mapping of cyclic data in AMCore is derived from the **ENI file**, where the information about the device's I/O data is specified, ensuring that each data item is correctly mapped according to its intended location in the network.

## Cyclic Data Map Information

In AMCore, cyclic data is mapped based on the information provided in the ENI file. The cyclic data refers to the periodic exchange of data between the EtherCAT master and slave devices. The ENI file plays a critical role in ensuring the correct mapping of this data to the correct addresses.

> [!TIP]
> AMCore uses the mapping provided in the ENI file to determine the amount of data each device will provide and accept in the cyclic packet.

## Configuration Requirements

The only configuration required for EtherCAT I/O support in AMCore is specifying the **starting address** for where the data is mapped. You need to define the starting address for each type of data (input, output, etc.) in the system's database configuration.

### Database Configuration

The database configuration contains the starting addresses for various data types. Here is a list of the key configuration parameters that AMCore uses to define the mapping:

- [Digital input base address](../../reference/parameter-reference.md#io-devices)
- [Digital output base address](../../reference/parameter-reference.md#io-devices)
- [Analog input base address](../../reference/parameter-reference.md#io-devices)
- [Analog output base address](../../reference/parameter-reference.md#io-devices)
- [String input base address](../../reference/parameter-reference.md#io-devices)
- [String output base address](../../reference/parameter-reference.md#io-devices)
- [Float input base address](../../reference/parameter-reference.md#io-devices)
- [Float output base address](../../reference/parameter-reference.md#io-devices)

These addresses are critical for correctly mapping the data from the EtherCAT slaves to AMCore's data structure. Once the starting addresses are configured, the system can automatically map the cyclic data from the EtherCAT network to the appropriate locations in the shared memory.

## Mapping Data Types to AMCore

Data is mapped to four supported data types: **int**, **bool**, **string**, and **float**. Since EtherCAT supports a variety of data types, not all of them can be directly mapped to these four AMCore types. Below is a table that shows the supported mappings from EtherCAT data types to AMCore data types, along with the unsupported types.

| EtherCAT Data Type | AMCore Data Type |
| ------------------ | ---------------- |
| Boolean            | bool             |
| Integer8           | int              |
| Integer16          | int              |
| Integer24          | int              |
| Integer32          | int              |
| Integer40          | Not Supported    |
| Integer48          | Not Supported    |
| Integer56          | Not Supported    |
| Integer64          | Not Supported    |
| Unsigned8          | int              |
| Unsigned16         | int              |
| Unsigned24         | int              |
| Unsigned32         | Not Supported    |
| Unsigned40         | Not Supported    |
| Unsigned48         | Not Supported    |
| Unsigned56         | Not Supported    |
| Unsigned64         | Not Supported    |
| Real32             | float            |
| Real64             | float            |
| Byte               | int              |
| Word               | int              |

### Data Conversion

It's important to note that some EtherCAT data types, such as **Integer40**, **Integer48**, and **Unsigned32**, are **not supported** by AMCore. In these cases, no direct mapping exists, and unsupported data types will be skipped during processing.

For supported data types, AMCore automatically handles the conversion according to the mappings provided in the table. Specifically:

- **Boolean** data is mapped to **bool** in AMCore.
- **Unsigned**, **Unsigned16**, and **Unsigned24** data are mapped to **int** in AMCore.
- **Integer8**, **Integer16**, **Integer24**, and **Integer32** data are mapped to **int** in AMCore.
- **Real32** and **Real64** data are mapped to **float** in AMCore.
- **Byte** and **Word** data are both mapped to **int** in AMCore.

AMCore simplifies the mapping process by only processing the supported EtherCAT data types, ensuring that the configuration effort is focused solely on setting the correct starting addresses.