# Data block mapping

The purpose of Data Block Mapping is to configure data transfers between Shared Memory and the process data areas (PDIN and PDOUT) of EtherCAT drive devices. This document describes the required database parameters and setup examples for using Data Block Mapping in the system.

Each data block mapping entry specifies:

* An **input** (source) and **output** (destination)
* The **type**, **device number**, and **object index**
* The **size** of the data transferred

## Restrictions

* Up to 45 mappings are supported (entries 1-45).
* Only the following combinations are allowed:
  * Shared Memory &rarr; Process Data OUT (PDOUT)
  * Process Data (PDIN/PDOUT) &rarr; Shared Memory
  * Process Data (PDIN/PDOUT) &rarr; Process Data OUT (PDOUT)
* **Shared Memory &harr; Shared Memory** mappings are not currently supported
* Output Data Block type cannot be of type PDIN.
* Both input and output types must be defined (cannot use one without the other)

## Configuration Parameters

1. Enable Flag

| Value | Meaning                      |
| ----- | ---------------------------- |
| -1    | Entry not used               |
| 0     | Entry defined but not active |
| 1     | Entry defined and active     |

```
*[data_block_entry].data_block.enabled : 1 
```

2. INPUT/OUTPUT Type

| Type | Meaning                   | Description                                                     |
| ---- | ------------------------- | --------------------------------------------------------------- |
| PD   | Process Data Input/Output | Sending data to the drive/Receiving data from the drive         |
| OPB  | Output Physical Boolean   | A section of Shared Memory that contains Booleans (bits/flags)  |
| IPB  | Input Physical Boolean    | A section of Shared Memory that contains Booleans (bits/flags)  |
| OPI  | Output Physical Integer   | A section of Shared Memory that contains 32-bit signed integers |
| IPI  | Input Physical Integer    | A section of Shared Memory that contains 32-bit signed integers |
| OFF  | Off                       | Don't perform a transfer                                        |

Both the **input** and **output** types must be specified:

```
*1.data_block_input.type : PD
*1.data_block_output.type : IPB
```

3. Specifying Targets

Defines the EtherCAT device involved in the mapping, using a **device number** (`DD<Y`>) and a **CoE object index**. The format must strictly follow the pattern: `DD<Y>.0x<Index><SubIndex>`.

Where:

* `<Y>` is the **device number**.
* `<Index>` is a 4-digit hexadecimal number (e.g., `6040`).
* `<SubIndex>` is a 2-digit hexadecimal number (e.g., `00`).
* The full index and subindex are concatenated and must be prefixed with `0x`.

Only **4-digit** (index only, subindex defaults to `00`) or **6-digit** (explicit index + subindex) hex values are allowed.
A 5-digit hex value is invalid and will raise an error.

An invalid object will also raise an error.

Valid Examples:

> [!NOTE]
> Valid Examples:<br>
> `DD1.0x604000`   &rarr; device 1, index 0x6040, subindex 0x00 <br>
> `DD3.0x8A0107`   &rarr; device 3, index 0x8A01, subindex 0x07 <br>
> `DD9.0x9F0710`   &rarr; device 9, index 0x9F07, subindex 0x10 <br>
> `DD6.0x1234F0`   &rarr; device 6, index 0x1234, subindex 0xF0 <br>

4. Start Location (for Shared Memory only)

Defines the starting point in shared memory (Boolean or Integer).

```
*1.data_block_input.start_location : 10
*1.data_block_output.start_location : 50
```

5. Size

The number of bytes to transfer.

```
*1.data_block_input.size : 2
*1.data_block_output.size : 2
```

> [!WARNING]
> Input and output sizes must match, or an error will be raised.

### Example Configurations:

1. Map Shared Memory to PD:

```
*17.data_block.enabled : 1

*17.data_block_input.type : IPB
*17.data_block_input.start_location : 100
*17.data_block_input.size : 4

*17.data_block_output.type : PD
*17.data_block_output.targets : DD1.0x604000,DD2.0x604000
*17.data_block_output.size : 4
```

This configuration transfers shared memory bits starting at `IPB100` to index `0x6040`, subindex `0x00` on devices `1` and `2`.

2. Map PD to Shared Memory:

```
*9.data_block.enabled : 1

*9.data_block_input.type : PD
*9.data_block_input.target : DD3.0x604100
*9.data_block_input.size : 4

*9.data_block_output.type : OPB
*9.data_block_output.start_location : 100
*9.data_block_output.size : 4
```
This configuration maps process data from index `0x6041`, subindex `0x00` of device `3` to shared memory starting at `OPB100`.

3. Map PD Input to PD Output:

```
*33.data_block.enabled : 1

*33.data_block_input.type : PD
*33.data_block_input.target : DD1.0x604000
*33.data_block_input.size : 2

*33.data_block_output.type : PD
*33.data_block_output.targets : DD2.0x604000,DD4.0x604000,DD5.0x604000
*33.data_block_output.size : 2
```

This configuration maps process data from index `0x6040`, subindex `0x00` of device `1` to the same index on devices `2`, `4`, and `5`.