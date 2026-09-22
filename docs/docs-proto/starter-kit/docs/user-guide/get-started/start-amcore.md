# Start AMCore

In AMCore 1.5, a single point entry to AMCore was introduced, which provides simplified setup, startup, and stop procedures.

This entry point is an executable named `amcore.exe` and is found in the folder defined by the environment variable `%amcore%`.

To start AMCore, you can simply execute (from the command line):

```console
"%amcore%amcore"
```

This will run setup (if required) and launch AMCore. If setup runs, a system restart may be required to launch AMCore. The quotation marks prevent spaces in the path (defined by `%amcore%`) causing issues.

## Command line interface

The following command line options are available for `amcore.exe`:

| Option&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;| Description                                                                                                                                                                                    |
| ------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `-version VALUE`   | Indicates which AMCore version to use. Can be shortened to `-v`.                                                                                                                               |
| `-start`           | Starts AMCore. If base mode is running, complete startup.                                                                                                                                      |
| `-start base`      | Starts AMCore in base mode. This advanced option is a partial startup that allows manipulation of parameters and variables.                                                                    |
| `-start device`  | Starts AMCore in device mode. This is a three-phase startup that pauses after device initialization to allow firmware download, then continues with full startup.                          |
| `-stop`            | Stops AMCore. This option will override all other options.                                                                                                                                     |
| `-setup`           | Forces setup to run.                                                                                                                                                                           |
| `-config FILEPATH` | Start AMCore with the configuration file located at FILEPATH. The path must not contain spaces, but can contain environment variables.<br><br>This option is available from AMCore 1.8 onward. |
| `-sim`             | Run in windows only, do not use hardware.                                                                                                                                                      |
| `-nohw`            | Simulation with INtime, without use of hardware.                                                                                                                                               |
| `-forcebl`         | Force bootloader download (EtherCAT only).                                                                                                                                                     |
| `-forcedl`         | Force firmware download (EtherCAT only).                                                                                                                                                       |
| `-passivedl`       | Run code download in an unattended mode - progress bar only (EtherCAT only).                                                                                                                   |
| `-plcc`            | Force the PLC to compile.                                                                                                                                                                      |
| `-options`         | Allows additional arguments to be passed to internal processes.                                                                                                                                |

If no arguments are supplied, then `-start` is assumed. If arguments are provided, then you must also specify `-start` if you want AMCore to run after the other options are processed.

> [!NOTE]
> You don't need to specify the version in most cases. If you don't provide the version, the active version runs. If no version has been activated, the highest version runs.

`amcore.exe` returns an exit code to indicate the success of the requested operation, as described in [amcore.exe exit codes](../troubleshoot/amcore-exe-exit-codes.md#amcoreexe-exit-codes).

### Examples

To start AMCore 1.8 when you have multiple versions installed (and run setup first if required):

```console
"%amcore%amcore" -start -v 2.0
```

To setup and then start AMCore 1.8 when you have multiple versions installed:

```console
"%amcore%amcore" -start -v 2.0 -setup
```

## Launch an application with AMCore

It is common that you may want to launch software that works with or depends on AMCore. To do this you should call/execute `amcore.exe` (with desired options) in sequence with your application executable and/or supporting software e.g. from a custom launcher, script or batch file.

Any command to start AMCore (e.g. `amcore.exe -start`) will not return until the startup has completed. This means that, if necessary, any launch sequence can wait for `amcore.exe` to return before running any software that depends on AMCore.

> [!NOTE]
> This approach is available in and recommended for AMCore 1.8 and above. For earlier AMCore versions, a target-specific batch file can optionally be used to launch software after AMCore has started (e.g. `PCC_start.bat`).