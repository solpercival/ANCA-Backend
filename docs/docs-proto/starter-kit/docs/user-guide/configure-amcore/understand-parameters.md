# Understand parameters

You can configure AMCore by providing a *parameter file* containing some *parameters*, which are persistent settings that apply to AMCore.

A parameter file is a text file containing one or more parameters. Each parameter is a key : value pair. Parameters are of 4 basic types: *boolean*, *integer*, *floating-point* or *string*.

AMCore supports a hierarchy of 6 parameter files, as shown in the following table.

| #   | Parameter file | Writeable? | Supplied by | Notes                                                |
| --- | -------------- | ---------- | ----------- | ---------------------------------------------------- |
| 5   | Test           | Read-only  | Users       | Generally used only for testing purposes.            |
| 4   | User           | Writeable  | Users       |                                                      |
| 3   | Oem            | Writeable  | Users       |                                                      |
| 2   | Mspec          | Read-only  | Users       |                                                      |
| 1   | Common         | Read-only  | Users       |                                                      |
| 0   | Gen            | Read-only  | AMCore      | Not configurable. Contains default parameter values. |

The parameter files have a fixed priority order as listed above - from the *test* file (highest priority) to the *gen* file (lowest priority). When querying a parameter, AMCore will search these files, in the order listed above, and return the first match that is found.

The first 5 files (*test*, *user*, *oem*, *mspec*, *common*) are for user configuration of AMCore. You can configure AMCore by providing one or more of these files, containing your desired parameter values. However, each file is optional, and they do not need to be supplied.

The final file (*gen*) is part of AMCore and provides default values for many parameters. This file is not user-configurable, but is listed for completeness.

AMCore provides interfaces that allow run-time writing of parameters to the *user* or *oem* parameter files. The remaining files are treated as read-only and may not be written via these interfaces.

The parameter file hierarchy, as shown above, allows a set of users to configure AMCore via a set of individual parameter files (one provided by each user).

## Configure locations for parameter files

You can customise the locations of the parameter files *test*, *user*, *oem*, *mspec* and *common*. You can specify the location (and name) of each parameter file via its corresponding *[configuration property](understand-configuration-properties.md#understand-configuration-properties)*, as shown in the following table.

| #   | Parameter file | Writeable? | Configuration property   | Default (legacy) location             |
| --- | -------------- | ---------- | ------------------------ | ------------------------------------- |
| 5   | Test           | Read-only  | `parameters.test.path`   | `<home folder>\misc\p_test.db`        |
| 4   | User           | Writeable  | `parameters.user.path`   | `<home folder>\misc\p_user.db`        |
| 3   | Oem            | Writeable  | `parameters.oem.path`    | `<home folder>\misc\p_oem.db`         |
| 2   | Mspec          | Read-only  | `parameters.mspec.path`  | `<home folder>\db\config\p_mspec.db`  |
| 1   | Common         | Read-only  | `parameters.common.path` | `<home folder>\db\config\p_common.db` |

If you want to add and/or modify some parameters, you should create a parameter file containing your custom parameter values, then set the corresponding configuration property (of data type: *string*) to the filepath of your parameter file. See [Understand configuration properties](understand-configuration-properties.md#understand-configuration-properties) for information on their usage.

If you customise the location of a parameter file, the file must exist in that location. If the file is missing, AMCore will not start and **AMCore.exe** will return an [error code](../troubleshoot/amcore-exe-exit-codes.md#startup-exit-codes). However, you can change this behaviour via the configuration property's `optional` *[attribute](understand-configuration-properties.md#adjust-how-configuration-properties-behave).* If you set `optional` to `true`, AMCore will ignore the file if it doesn't exist, and will instead start normally. In this case, the specified location will be ignored and the configuration property will revert to the value specified in any included configuration file(s) or to its default value. If you set `optional` to `false` (or omit it), the file must exist.

> [!WARNING]
> If you set `optional` to `true`, AMCore won't warn you if the corresponding parameter file is missing, which could lead to undetected errors. For this reason, you should avoid using the `optional` attribute wherever possible.

Each parameter file has a default location, as shown in the table. If you don't customise the location of a parameter file (via its configuration property), AMCore will instead look for that file in its default location (where the file doesn't need to exist).

> [!TIP]
> You should specify the locations of your parameter file(s) via their corresponding configuration propert(ies). You shouldn't rely on default locations for parameter files, since these exist primarily for legacy reasons.

> [!NOTE]
> When AMCore's Diagnostic Tool is run, it will automatically capture each parameter file from its (last) configured custom location.

## Automatic creation of writeable parameter files

You can use AMCore to write to the writeable parameter files (*user* and *oem*) without first creating these files, as AMCore will automatically create these files when required.

If you don't specify a custom location for a writeable parameter file (via its configuration property), and that file is absent from its default location (see table above), AMCore will automatically create a blank copy of that parameter file (in an AMCore-defined location). You can then use AMCore's standard interfaces to write parameters to (and subsequently read parameters from) that newly-created file.

This feature allows multiple software applications to write to a single parameter file, without first requiring an individual (pre-nominated) application to install a blank copy of that file. For example, a machine may run multiple software applications that each generate some machine configuration parameters, which they then save to the *user* parameter file. In this situation, it may be unclear who is responsible for creating the initial (blank) *user* file (and unclear when this should occur), so the applications could instead rely on AMCore to automatically generate this file. The individual applications could then simply write to the *user* file, when desired, without first needing to create the file.

> [!NOTE]
> Automatic creation applies only to the writeable parameter files. It would not be meaningful to automatically create a blank copy of a read-only parameter file, as all queries to this file would fail anyway.