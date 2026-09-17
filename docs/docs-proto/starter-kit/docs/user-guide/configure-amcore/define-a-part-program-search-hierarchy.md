# Define a part program search hierarchy

You can configure AMCore by defining a *part program search hierarchy*, which is an ordered list of folders in which AMCore will search for your part programs. This search hierarchy tells AMCore where to find your programs.

The main steps to use a part program search hierarchy are as follows:

1. [Define a search hierarchy](#define-a-search-hierarchy) This is an ordered list of folders.
2. Store your part programs in these folders (including within their subfolders).
3. [Run programs using the search hierarchy](#run-programs-using-the-search-hierarchy). When you use a supported interface to run a part program, AMCore will search the configured hierarchy to locate the relevant program.

A part program search hierarchy provides the following benefits:

- You can run part programs via [relative filepaths](#eppl-callp-plc-devices-pp_run-and-cnc-connect) (relative to your specified hierarchy folders).
- You can [override part programs](#override-part-programs) supplied by other users (without modifying their original files) in order to customise an existing system.

> [!NOTE]
> You don't have to define a part program search hierarchy. However, in that case, you must run all part programs via [absolute filepaths](#eppl-callp-plc-devices-pp_run-and-cnc-connect), so AMCore knows where to find them.

## Define a search hierarchy

You can define your part program search hierarchy via the *[configuration property](../configure-amcore/understand-configuration-properties.md#understand-configuration-properties)* `programs.paths` (data type: *array of strings*).

You should set this configuration property to a list of folder paths, in the order that you want them to be searched. See [Understand configuration properties](../configure-amcore/understand-configuration-properties.md) for information on their usage.

You can then store part programs in the specified folders (including within their subfolders) and use AMCore to run them.

You can extend another user's search hierarchy by creating a *configuration file* that includes their existing configuration file. See [Override configuration properties](../configure-amcore/understand-configuration-properties.md#override-configuration-properties) for an example. Your `programs.paths` (which lists your part program folders) will be prepended to their existing `programs.paths` - creating a combined search hierarchy in which your folders take priority over their folders.

> [!NOTE]
> The part program search hierarchy may include any number of folders. The list may include 0 or more folders and does not have a maximum size.

> [!NOTE]
> The search order matches the order in which folders are listed in the configuration file(s). You don't specify a numbered position for each folder.

> [!NOTE]
> AMCore does not require the specified folders to exist. If a folder does not exist, it will simply be skipped when searching the hierarchy (just like a folder that exists but does not contain the relevant part program file).

> [!WARNING]
> AMCore's legacy part program folders (e.g. `PP`, `PPSYS` and `MISC`) and the corresponding parameters (`dirs.pp`, `dirs.cc`, `dirs.espp` and `dirs.espp_special`) are considered to be deprecated. AMCore does not require these parameters to be defined. You should define your part program folders via the part program search hierarchy, rather than relying on these legacy folders.

## Run programs using the search hierarchy

You can use the following interfaces to run part programs using the configured search hierarchy:

- EPPL subprogram call (`CALLP`)
- PLCL sub-part-program devices (e.g. `SPPGG`)
- PP\_RUN
- CNC Connect
- G-Codes
- M-Codes

See [Run part programs](../use-amcore/run-part-programs.md#run-part-programs) for general information on using these interfaces.

The following subsections describe AMCore's behaviour, including its searching of the configured search hierarchy, when running a part program via each of these interfaces.

In the following examples, we assume that the part program search hierarchy has been configured (via your configuration file and its nested included files (if any)) to a list of `N` *hierarchy folders* (in priority order):

- `[hierarchy path 1]` (highest priority, searched first)
- ...
- `[hierarchy path N]` (lowest priority, searched last)

You can use the part program search hierarchy to run part programs that are stored in the hierarchy folders themselves, or in subfolders of the hierarchy folders

### EPPL CALLP, PLC Devices, PP\_RUN and CNC Connect

If you run a part program via a **relative filepath**, AMCore will search the configured search hierarchy for the corresponding part program:

- You can use these interfaces to run a part program via a relative filepath: `"[subfolder path]/<filename>"`
- Here, `[subfolder path]` is optional and may have 0 or more levels. The filepath may optionally be specified using environment variables, and may optionally have a leading slash.
- In this case, AMCore will search the following locations for the relevant part program, and run the first program that it finds (if any):
  - `[hierarchy path 1]\[subfolder path]\<filename>`
  - ...
  - `[hierarchy path N]\[subfolder path]\<filename>`

> [!NOTE]
> PP\_RUN (a command-line utility) and CNC Connect (an API) do not use the current working directory to resolve relative filepaths. Instead, they search the configured search hierarchy for the corresponding part program, as described above.

Alternatively, if you run a part program via an **absolute filepath**, AMCore will run the exact part program that you have specified:

- You can use these interfaces to run a part program via an absolute filepath: `"<absolute path>"`
- The filepath may optionally be specified using environment variables.
- In this case, AMCore will run the specified part program (if it exists) - and will not search the configured search hierarchy.

> [!TIP]
> You can use an absolute filepath to run a part program that resides either inside or outside the configured search hierarchy. This will prevent your specified program from being overridden by (other) programs in the search hierarchy.

### G-Codes

If your part program includes a [(canned cycle) G-Code](../use-amcore/run-part-programs.md#using-a-g-code), AMCore will search the configured search hierarchy for the corresponding part program:

- Your part program can include a (canned cycle) G-Code: `g# i0`
- Here, `#` is the G-Code number. The (canned cycle) G-Code (`g#`) must be programmed with at least one parameter (`i0`) or dimension word (`x0`) - or it will simply be ignored.
- In this case, AMCore will search the following locations for a *canned cycle* (a part program) named `g#.pp`, and run the first program that it finds (if any):
  - `[hierarchy path 1]\g#.pp`
  - ...
  - `[hierarchy path N]\g#.pp`
- You can thus customise a G-Code (`g#`) by creating a canned cycle (part program) named `g#.pp` in a (root) hierarchy folder from your configured search hierarchy.
- This applies only to G-Codes that trigger user-supplied canned cycles. Other G-Codes are *preparatory words* that are reserved by AMCore and do not trigger part programs.

### M-Codes

If your part program includes a [(mode 4) M-Code](../use-amcore/run-part-programs.md#using-an-m-code), AMCore will search the configured search hierarchy for the corresponding part program:

- Your part program can include a (mode 4) M-Code: `m#`
- Here, `#` is the M-Code number.
- In this case, AMCore will search the following locations for a part program named `m#.pp`, and run the first program that it finds (if any):
  - `[hierarchy path 1]\m#.pp`
  - ...
  - `[hierarchy path N]\m#.pp`
- You can thus customise an M-Code (`m#`) by creating a part program named `m#.pp` in a (root) hierarchy folder from your configured search hierarchy.
- This applies only to M-Codes that are configured to use mode 4 (trailing subprogram call), and are thus implemented via part programs. Other M-codes (modes 1-3 and 5-7) are instead implemented via the PLC and do not trigger part programs.

## Override part programs

You can use the part program search hierarchy to override part programs supplied by other users (without modifying their original files) in order to customise an existing system. You can do this as follows:

1. *Inherit the existing search hierarchy*. Create a configuration file that includes the existing configuration file, to inherit the existing `programs.paths`.
2. *Extend the search hierarchy*. Add the configuration property `programs.paths`, which lists your hierarchy folder(s), to your configuration file.
3. *Override a part program*. Create a part program in your hierarchy folder, with the same filename (and subfolder structure) as the original part program, to implement your custom behaviour.

> [!TIP]
> You can use the part program search hierarchy to override custom G-Codes and M-Codes supplied by other users.
> In step 3, you should create a part program in your (root) hierarchy folder, with the same filename (`g#.pp` or `m#.pp`) as the original part program, to implement your custom behaviour.

You can arrange your part programs into "namespaces" by storing them in subfolders of your hierarchy folders. When inheriting and overriding part programs supplied by other users, we recommend using subfolders to avoid unintentional overrides (while still allowing deliberate overrides):

- You should create a uniquely-named subfolder (of your hierarchy folder) to contain your part programs. You should choose a subfolder name that hasn't been used by existing users (whom you are inheriting from).
- If you are creating a new part program (and not overriding an existing part program): You should save this part program in your uniquely-named subfolder. This minimises the risk of accidentally overriding part programs inherited from existing users (including any programs they may provide in the future, via updates to their software applications).
- If you are overriding an existing part program: You must match the subfolder and filename of the existing part program, as described above.