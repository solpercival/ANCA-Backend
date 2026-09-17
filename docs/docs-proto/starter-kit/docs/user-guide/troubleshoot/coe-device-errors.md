# CoE Device Errors

DRAFT

## Overview

This section covers log locations for drive errors, error descriptions, and current recovery steps.

Typically, the Ethercat Master application is responsible for detecting and capturing errors or state changes directly and then forwarding those onto the DSA application where they may be either raised as error messages or forwarded on elsewhere. At this time, all messages end at the DSA application, where they are either displayed as the red EP popup windows, or printed to the log.

## Log Files

### DSA log file

Generally, the log messages printed out in the DSA log file will mirror those displayed in EP popup messages. However, some informational messages and unhandled errors may only be found in the log file, and so it can be a useful place to look when performing drive related troubleshooting.

**Location:** `%amcore%/PCC/dsa.log`

### Ethercat Master log file

Log messages that are not yet forwarded onto DSA and often additional Ethercat master specific information is provided in the Ethercat master log file. Not all errors are handled at this time, but generic error/message handlers do exist that print out debug information that can be used in the meantime.

**Location:** `%amcore%/PCC/ecatmaster.log`

## Errors

For all errors described below, a red popup message is provided alongside the error in the log when applicable.

Errors have the concept of severity and the way each severity level is handled determines what kind of user messaging is provided and if any change to Ethercat bus state is necessary.

Currently, we provide the following three severity levels:

| **Severity Level** | **Description** |
| --- | --- |
| Error | A state change that cannot be ignored by the user and potentially requires the Ethercat bus to be taken down to safe op state |
| Warning | A state change that could be indicative of an issue, but doesn't stop the drive from operating normally |
| Info | A state change that is purely informational, i.e. no action or acknowledgement is required |

### Emergency Error

**Severity:** Info or Error (based on error code)

Note that emergencies with an error code set to zero is an informational message that some drives raise when it has successfully recovered from an emergency. In the informational message case, no error is raised and the severity is Info.

**Data:**

| Name | Description |
| --- | --- |
| Error code | Specific error code from the drive as reported by the `0x1001:00` CoE object |
| Error register | Current error register state as reported by the `0x1004:00` CoE object |
| Error data | 5 bytes of additional error information which can be populated by the drive manufacturer. Further information on this data needs to be sought from the drive manufacturer manual |

**Locations:**

- Found in DSA log
- Produces a red EP popup window

**Resolution:**  
In the case of an emergency with informational severity, there is nothing to do but acknowledge the message.

In the case that it is an error, typically the drive will be stuck in an error state and can only be recovered by reinitialising the Ethercat bus, or restarting the system.

### Frame Response Error

Frame response errors are raised when an Ethercat frame, either cyclic or non-cyclic, received by the master are in some way malformed or unexpected. The specifics of the error can be further determined via the 'Error type' data that is returned with the error.

**Severity:** Error

**Data:**

| Name | Description |
| --- | --- |
| Is cyclic frame | is the frame cyclic or non-cyclic |
| Error type | Type of frame response error |
| Expected index value | Index value that was expected |
| Actual index value | Index value that was received |
| Lost cyclic frames | Number of frames lost during communication |
| Cyclic task ID | Identifier of the affected cyclic task |

The error type can be one of the following:

- Undefined - Default error state
- No Response - Device failed to respond to the frame
- Wrong Index - Received frame had incorrect index
- Unexpected - Unexpected frame response received
- Frame Retry - Frame transmission was retried
- Retry Fail - Frame retry attempts were exhausted
- Foreign Source MAC - Frame received from unexpected MAC address
- Non-EtherCAT Frame - Received frame was not EtherCAT protocol
- CRC - Frame failed CRC check

**Locations:**

- Found in DSA log
- Produces a red EP popup window

**Resolution:**  
Sometimes these errors are spurious, and the drive is able to recover itself. If multiple of these errors continue to be raised, often this will result in an Emergency and the same recovery procedure is required, i.e. a system restart in most cases.

### Distributed Clock Master Sync

The distributed clock master sync message tells us of a state change in synchronisation, i.e. if the distributed clock deviates from synchronisation by a threshold.

**Severity:** Info or Warning (based on sync state)

**Data:**

| Name | Description |
| --- | --- |
| Sync state | Current synchronization status |
| Current deviation | Present time deviation in microseconds |
| Average deviation | Mean time deviation in microseconds |
| Maximum deviation | Largest observed time deviation in microseconds |

For each deviation value, the direction of deviation is indicated by the sign of the value, i.e. positive values mean the clock is measured as leading, and negative values indicated the clock is lagging.

**Locations:**

- Found in DSA log

**Resolution:**  
You normally don't need to do anything for this message as it is informational only.

### Distributed Clock Device Sync

Similar to the Distributed Clock Master Sync, but with respect to a device. Each device in the network can provide its own message.

**Severity:** Info or Warning (based on sync state)

**Data:**

| Name | Description |
| --- | --- |
| Sync state | Device synchronization status |
| Device station address | Network address of the device |
| Device name | Identifier name of the device |
| Auto-increment address | Automatically assigned device address |
| Deviation | Time deviation in microseconds (+ or -) |

**Locations:**

- Found in DSA log

**Resolution:**  
Normally don't need to do anything for this one as it is informational only.

### Distributed Clock Status

**Severity:** Info or Warning (based on status code)

**Data:**

| Name | Description |
| --- | --- |
| Status code | Hexadecimal status code of the DC |

**Locations:**

- Found in DSA log

**Resolution:**  
Normally don't need to do anything for this one as it is informational only.

### Master State Changed

Alerts us to when the Master operational state has changed e.g. from Op to SafeOp.

**Severity:** Info

**Data:**

| Name | Description |
| --- | --- |
| Old state | Previous state of the master |
| New state | Current state of the master |

**Locations:**

- Found in DSA log

**Resolution:**  
Normally don't need to do anything for this one as it is informational only.

### Device Unexpected State Error

A device will raise a device unexpected state error when its operational state no longer matches that of the Master.

**Severity:** Error

**Data:**

| Name | Description |
| --- | --- |
| Device station address | Network address of the device |
| Device name | Vendor name of the device |
| Auto-increment address | Automatically assigned device address (note: this is provided in addition to the station address, since the station addresses may not have been assigned if the system hasn't left the init state) |
| Current state | Actual operational state of the device |
| Expected state | Operational state the device should be in |

**Locations:**

- Found in DSA log
- Produces a red ep popup

**Resolution:**  
Almost always requires a system restart, and in some cases, a drive restart.

### Other errors

TODO

- I don't think we need to or should list out all errors available in the logs, the ones above are at least ones we'd probably want to end up forwarding on to alarm controller or something and hence could be relevant to users.