# Device firmware upgrade

AMCore supports uploading firmware to EtherCAT slave devices using the File over EtherCAT (FoE) protocol. Firmware can be uploaded in three ways:

1. **Automatic mode** - headless version check and upload during startup
2. **Interactive mode** - manual commands via the `device-firmware-upload` tool
3. **CNCC SDK** - programmatic upload from any C/C++ application

## Prerequisites

* The firmware binary file must be accessible on disk.
* The fieldbus must be in INIT or PREOP state - **not** SAFEOP or OP.

### AMCore device mode

Firmware uploads require the EtherCAT fieldbus to be in a non-operational state (INIT or PREOP). To achieve this, start AMCore with the `-start device` flag:

```bat
AMCore.exe -start device
```

This starts the Device Administrator and brings the fieldbus to PREOP without continuing to SAFEOP/OP. The system stays in this state, giving you a window to inspect and upload firmware before the machine goes operational.

After firmware work is complete, you must either:

* **`AMCore.exe -start`** - continue the normal startup sequence (fieldbus transitions to OP). Use this when firmware uploads succeeded.
* **`AMCore.exe -stop`** - shut down AMCore. Use this when firmware uploads failed and the machine should not proceed.

> [!IMPORTANT]
> If you call `AMCore.exe -start` without first calling `AMCore.exe -start device`, the system proceeds directly to OP and firmware uploads will be rejected with `CNCCRESULT_INVALID_FIELDBUS_STATE`.

## Automatic mode (startup integration)

The `device-firmware-upload.exe --auto` command runs a headless workflow suitable for integration into machine startup scripts. It:

1. Discovers all devices on the EtherCAT bus
2. Compares each device's actual firmware version against the expected version from the DBA
3. Uploads firmware for any mismatched devices
4. Polls until all uploads complete
5. Verifies by re-reading firmware versions
6. Exits with a status code

The typical startup pattern is: enter device mode, run the firmware tool, then continue or stop based on the result.

### Startup script example

```bat
REM 1. Start AMCore in device mode (fieldbus enters PREOP, does not go to OP)
call AMCore.exe -start device

REM 2. Run automatic firmware check and upload
call device-firmware-upload.exe --auto --log-level info

REM 3. Check the result and decide how to proceed
if %errorlevel% NEQ 0 (
    echo Firmware upload failed with code %errorlevel%
    REM Upload failed - shut down AMCore, do not go operational
    call AMCore.exe -stop
    exit /b %errorlevel%
)

REM 4. Firmware is OK - continue normal startup (fieldbus transitions PREOP -> OP)
call AMCore.exe -start
```

### Exit codes

| Code | Meaning |
|------|---------|
| 0 | All firmware up to date or updated and verified |
| 2 | Upload failed |
| 3 | No devices found (treated as success) |
| 4 | Device query failed |
| 5 | Post-upload version verification failed |

### DBA configuration

Each device that requires firmware management needs two DBA parameters:

| Key | Class | Description | Example |
|-----|-------|-------------|---------|
| `<dev>.dsd_firmware_version` | `dsd_firmware_version` | Expected firmware version | `"1.2.3"` |
| `<dev>.dsd_firmware_path` | `dsd_firmware_path` | Full path to firmware file | `"C:\firmware\drive_v1.2.3.bin"` |

Where `<dev>` is the logical device number (e.g., `1`, `2`).

**Example DBA entries for device 1:**

```
*1.dsd_firmware_version : 1.2.3
*1.dsd_firmware_path : C:\firmware\drive_v1.2.3.bin
```

If `dsd_firmware_version` is not configured for a device, that device is skipped.

### Command-line options

```
device-firmware-upload.exe [OPTIONS]
```

| Option | Description | Default |
|--------|-------------|---------|
| `--auto` | Run headless firmware check/upload workflow | (interactive mode) |
| `--log-level` | Log level: `debug`, `info`, `warning`, `error`, `fatal` | `info` |
| `--help` | Display help and exit | |

### Logging

In auto mode, logs are written to `device_firmware_upload.log` using a rolling file logger. The log level is configurable via `--log-level`.

## Interactive mode

Without `--auto`, the tool starts an interactive command-line session where you can run firmware operations manually.

```
device-firmware-upload.exe
```

### Available commands

| Command | Short | Description |
|---------|-------|-------------|
| `--firmware -l <dev> -p <path>` | `-f` | Upload firmware to a device |
| `--actual-firmware -l <dev>` | `-af` | Print actual firmware version from device |
| `--expected-firmware -l <dev>` | `-ef` | Print expected firmware version from DBA |
| `--upload-status` | `-us` | Get upload progress (all devices if `-l` omitted) |
| `--upload-poll` | `-up` | Poll upload progress until complete |
| `--upload-abort -l <dev>` | `-ua` | Abort an ongoing upload |
| `--quit` | `-q` | Exit the program |
| `--help` | `-h` | Show help |

### Example: upload firmware to a single device

```
> -f -l 1 -p C:\firmware\drive_v1.2.3.bin
Uploading firmware to device 1...
Firmware path: C:\firmware\drive_v1.2.3.bin
Firmware file size: 524288 bytes
Using absolute path: C:\firmware\drive_v1.2.3.bin

Initiating firmware upload...
Upload started successfully.

> -up -l 1
Device 1: [########--------------------------------] 20% (104858/524288 bytes) IN PROGRESS
Device 1: [####################--------------------] 50% (262144/524288 bytes) IN PROGRESS
Device 1: [########################################] 100% (524288/524288 bytes) COMPLETE
```

### Other commands

```
> -af -l 1
Device 1: actual firmware version: 1.1.0

> -ef -l 1
Device 1: expected firmware version: 1.2.3

> -ua -l 1
Device 1: upload aborted.
```

Upload to multiple devices in one command, then poll all active uploads:

```
> -f -l 1 -p C:\firmware\drive_v1.2.3.bin -l 2 -p C:\firmware\io_v2.0.1.bin
> -up
```

## CNCC SDK (C API)

For programmatic control, use the CNCC SDK firmware upload functions. The typical workflow is: get a device handle, start an asynchronous upload, poll for progress, and free the handle. See the SDK documentation for complete type definitions, code examples, and error codes.

| Function | Description |
|----------|-------------|
| `CnccDeviceGetByLogical(device_number, &handle)` | Get a device handle by logical device number |
| `CnccDeviceUploadStartAsync(handle, filename)` | Start an asynchronous firmware upload |
| `CnccDeviceUploadGetProgress(handle, &progress)` | Poll upload state and byte counters |
| `CnccDeviceUploadAbort(handle)` | Cancel an in-progress upload |
| `CnccDeviceGetVersion(handle, &version)` | Read the current firmware version |
| `CnccDeviceFreeDevice(&handle)` | Free the device handle |

## Constraints and limitations

Firmware uploads use the FoE (File over EtherCAT) mailbox protocol. The target device is transitioned to BOOTSTRAP mode for the transfer, then restored to INIT on completion. If the fieldbus was in PREOP, it is cycled through INIT and back to PREOP to trigger EEPROM validation on all devices.

* **Concurrent uploads** - multiple devices can be uploaded simultaneously. However, a new upload cannot start while the post-upload fieldbus recovery cycle (PREOP&rarr;INIT&rarr;PREOP for EEPROM validation) is in progress. The system returns `CNCCRESULT_BUSY` until the cycle completes.
* **Fieldbus state** - uploads are only possible when the fieldbus is in INIT or PREOP. The system must not be in operational mode.
* **File path** - the firmware file path must be accessible from the AMCore host machine. Use absolute paths for reliability.
* **Upload duration** - large firmware files may take several minutes to transfer. The automatic mode has a 10-minute timeout by default.
* **Post-upload verification** - after firmware upload, the device may need a power cycle or fieldbus reinitialisation before the new firmware version is readable via `CnccDeviceGetVersion`.
