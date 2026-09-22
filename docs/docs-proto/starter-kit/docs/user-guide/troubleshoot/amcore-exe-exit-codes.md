# AMCore.exe exit codes

**AMCore.exe** is AMCore's entry point. It is used to setup, start and stop AMCore, as described in [Start AMCore](../get-started/start-amcore.md#start-amcore)

AMCore.exe returns an exit code to indicate the success of the requested operation. When an error occurs, this exit code may indicate the nature of the error.

Different operations (setup, startup, etc.) have different sets of exit codes.

## Setup exit codes

| Exit code | Description |
| --- | --- |
| 0   | Setup succeeded. |
| 1   | Setup failed. |

## Startup exit codes

| Exit code | Description |
| --- | --- |
| 0   | Startup succeeded. |
| 1   | Startup failed for an unknown reason. |
| 10001 | Processing of configuration properties failed for an unknown reason. |
| 10002 | Failed to parse command-line arguments. |
| 10003 | Failed to launch AMCore for an unknown reason. |
| 10004 | Failed to resolve a configuration file's path to an absolute filepath. |
| 10005 | Failed to open a configuration file. |
| 10006 | Failed to parse a configuration file. |
| 10007 | A configuration file has an invalid version. |
| 10008 | A configuration file contains a configuration property that is unrecognised. |
| 10009 | A configuration file contains a configuration property of an incorrect type. |
| 10010 | A configuration file contains a configuration property that cannot be resolved to an absolute filepath. |
| 10011 | Failed to update a configuration property for a parameter file. |
| 10012 | A parameter file is missing from its configured custom location. |
| 10013 | Failed to create a writeable parameter file. |
| 10014 | Failed to set AMCore's configuration properties. |
| 10015 | AMCore is already running. |
| 10016 | A configuration file contains an invalid include entry. |
| 10017 | A configuration file has been recursively included. |
| 10018 | A configuration file contains a configuration property with an invalid attribute. |
| 11001 | Failed to resolve a log file's path. |
| 11002 | Unsupported Windows code page (Unicode UTF-8).<br><br>(Please disable "Beta: Use Unicode UTF-8 for worldwide language support" under Windows Region Settings.) |
| 11003 | Unsupported INtime version. |

> [!NOTE]
> In AMCore 1.7 and earlier, the only startup exit codes are 0 (startup succeeded) or 1 (startup failed).