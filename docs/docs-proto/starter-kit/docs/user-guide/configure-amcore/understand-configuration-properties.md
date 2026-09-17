# Understand configuration properties

You can configure AMCore by providing a *configuration file* containing some *configuration properties*, which are settings that apply to the current AMCore session.

To do this, run **AMCore.exe** to start AMCore with the optional command-line argument `-config <filepath>`, where `<filepath>` is the path of your configuration file.

A configuration file is in JSON format and contains one or more configuration properties. Each configuration property is a name : value pair. Configuration properties are of 5 basic types: *boolean*, *integer*, *floating-point*, *string* or *array of strings*.

This section describes how to use configuration properties. For a list of all available configuration properties, refer to the [Configuration property reference](../reference/configuration-property-reference.md#configuration-property-reference).

## Example: Use a *string* configuration property

You can specify a custom location for the *test* parameter file via the configuration property `parameters.test.path`, which has the data type *string*.

You can do this by starting AMCore as follows:

**console:**

```console
C:\TEST>"%AMCore%AMCore.exe" -start -config example1.json
```

where your configuration file `C:\TEST\example1.json` contains:

```json
{
    "version":                 "1.0.0",

    "parameters.test.path":    "MyParametersFolder/myTestFile.db"
}

```

The property `parameters.test.path` specifies a custom filepath for the *test* parameter file: `C:\TEST\MyParametersFolder\myTestFile.db`.

## Example: Use an *array of strings* configuration property

You can specify custom locations for part program files via the configuration property `programs.paths`, which has the data type *array of strings*.

You can do this by starting AMCore as follows:

**console:**

```console
C:\TEST>"%AMCore%AMCore.exe" -start -config example2.json
```

where your configuration file `C:\TEST\example2.json` contains:

```json
{
    "version":                 "1.0.0",

    "programs.paths":          [
                                   "MyProgramFolder1/",
                                   "MyProgramFolder2/",
                                   "MyProgramFolder3/"
                               ]
}

```

The property `programs.paths` specifies a custom list of folder paths, which will be searched when activating part program files:

- `C:\TEST\MyProgramFolder1\`
- `C:\TEST\MyProgramFolder2\`
- `C:\TEST\MyProgramFolder3\`

## Usage

The command-line path `<filepath>` must be a valid path to a configuration file. This path may take the following forms:

- May be an absolute or relative path.
- May contain environment variables.
- Must not contain spaces.
- Folders may be delimited with forward slashes `/` or backslashes `\`.

> [!TIP]
> If the absolute path of your configuration file contains one or more spaces, you should change your working directory then specify `<filepath>` using a relative path, to ensure that `<filepath>` does not contain any spaces.
> 
> (Alternatively, you can specify `<filepath>` using an environment variable that contains the absolute path. However, you must ensure that the environment variable is not expanded before `<filepath>` is passed to AMCore.exe.)

Some configuration properties (such as `parameters.test.path` and `programs.paths`) specify custom paths for certain files or folders. These paths may take the following forms:

- May be absolute or relative paths.
- May contain environment variables.
- May contain spaces.
- Folders may be delimited with forward slashes `/` but not backslashes `\`.

> [!CAUTION]
> Do not use backslashes `\` in your configuration file. Backslashes have special meaning in the JSON file format, so AMCore may be unable to correctly parse your file. You should delimit folders with forward slashes `/` to avoid such errors.

All configuration properties are optional. If you don't set (or [inherit](#override-configuration-properties)) some properties, they will revert to their default values. For example:

- If you don't supply a configuration file (by omitting the option `-config <filepath>`), all properties will revert to their default values.
- If you supply a configuration file that contains a subset of the available properties, any omitted properties will revert to their default values.

Configuration properties are set during AMCore startup and apply to the current AMCore session. Each time you start AMCore, you can specify different values for some or all of the properties, if desired.

Configuration properties don't retain values that were specified during previous AMCore startups. Upon a new startup, if you don't set (or inherit) a given property, that property will instead revert to its default value. (When AMCore is offline, properties will retain their values from the last AMCore session. See [When AMCore is offline](#when-amcore-is-offline).)

You should begin every configuration file with a `version` entry, which specifies the file's format: 

```json
    "version":                 "1.0.0",

```

The original file format is `1.0.0` and the latest is `2.1.0`.

Where a minimum `version` is stated (below), that feature can only be used in configuration files whose `version` is equal to or higher than the minimum. Where no minimum `version` is stated, that feature can be used in configuration files with any valid `version`.

## Override configuration properties

Your configuration file can include another configuration file, to inherit any configuration properties from that included file. In fact, configuration files may be nested (to any desired depth) by including files within files, etc. Your properties (as specified in your configuration file) will take priority over any included properties (as specified in any nested included files).

### Example: Nested configuration files

You can override some configuration properties, using nested configuration files, by starting AMCore as follows:

**console**

```console
C:\TEST>"%AMCore%AMCore.exe" -start -config example3A.json
```

where your configuration file `C:\TEST\example3A.json` contains:

```json
{
    "version":                 "1.0.0",

    "include":                 "example3B.json",

    "parameters.test.path":    "MyParametersFolder/myTestFile.db",

    "parameters.user.path":    "MyParametersFolder/myUserFile.db",

    "programs.paths":          [
                                   "MyProgramFolder1/",
                                   "MyProgramFolder2/"
                               ]
}

```

and its included file `C:\TEST\example3B.json` contains:

```json
{
    "version":                 "1.0.0",

    "parameters.test.path":    "MyParametersFolder/myOtherFile.db",

    "parameters.oem.path":     "MyParametersFolder/myOemFile.db",
	
    "programs.paths":          [
                                   "MyProgramFolder3/",
                                   "MyProgramFolder4/"
                               ]
}

```

In this case, the resultant values of the properties are:

- `parameters.test.path`: `C:\TEST\MyParametersFolder\myTestFile.db`
- `parameters.user.path`: `C:\TEST\MyParametersFolder\myUserFile.db`
- `parameters.oem.path`: `C:\TEST\MyParametersFolder\myOemFile.db`
- `programs.paths`:
  - `C:\TEST\MyProgramFolder1\`
  - `C:\TEST\MyProgramFolder2\`
  - `C:\TEST\MyProgramFolder3\`
  - `C:\TEST\MyProgramFolder4\`

### Values of overridden configuration properties

The configuration properties specified in a configuration file (e.g. `example3A.json`) take priority over those specified in its included files (e.g. `example3B.json`). However, the mechanism for resolving these priorities depends on the data type of each property.

*Boolean*, *integer*, *floating-point* or *string*:

- If a property of type *boolean*, *integer*, *floating-point* or *string* is specified both in your configuration file and in an included configuration file, your value will override the included value.
- In Example 3, the final value of `parameters.test.path` is:
  - `C:\TEST\MyParametersFolder\myTestFile.db`
- This is because the value from `example3A.json` (`MyParametersFolder/myTestFile.db`) overrides the value from `example3B.json` (`MyParametersFolder/myOtherFile.db`).

*Array of strings*:

- If a property of type *array of strings* is specified both in your configuration file and in an included configuration file, your array will be prepended to the included array.
- In Example 3, the final value of `programs.paths` is:
  - `C:/TEST/MyProgramFolder1/`
  - `C:/TEST/MyProgramFolder2/`
  - `C:/TEST/MyProgramFolder3/`
  - `C:/TEST/MyProgramFolder4/`
- This is because the array from `example3A.json` (`[MyProgramFolder1/, MyProgramFolder2/]`) is prepended to the array from `example3B.json` (`[MyProgramFolder3/, MyProgramFolder4/]`).

### Configuration by multiple users

You can use a nested configuration file to override an AMCore configuration supplied by another user (without modifying their original files), in order to customise an existing system. Your configuration file would include their configuration file - to inherit their configuration properties, then optionally override some or all of those inherited properties.

A set of users may thus configure AMCore via a set of nested configuration files (one provided by each user). For example, a software application could specify its AMCore configuration by providing a configuration file containing some configuration properties. An OEM, who was customising that software application for their own use, could then alter or extend the AMCore configuration inherited from the application. The OEM would provide their own configuration file, which would include the application's configuration file - and would optionally override some properties and/or specify other properties.

### Optional includes

Normally, if your specified configuration file doesn't exist, or one of its nested included files doesn't exist, AMCore will not start and **AMCore.exe** will return an [error code](../troubleshoot/amcore-exe-exit-codes.md#startup-exit-codes).

However, if you flag an included file as *optional*, AMCore will ignore that file if it doesn't exist, and will instead start normally.

In the above example, the configuration file `example3A.json` could be modified as follows:

```json
    "version":                 "2.0.0",

    "include":                 {"value":"example3B.json", "optional":true},

```

In this case, the included file `example3B.json` is optional. If `example3B.json` exists, it will be included as normal. But if `example3B.json` doesn't exist, it will simply be ignored.

> [!WARNING]
> If you flag an included file as *optional*, AMCore won't warn you if the file is missing, which could lead to undetected errors. For this reason, you should avoid using optional includes wherever possible.

> [!NOTE]
> Your configuration file must have a minimum `version` of `2.0.0` to use optional includes.

### Multiple includes

Your configuration file can include *multiple* configuration files, to inherit configuration properties from all the included files.

In the above example, the configuration file `example3A.json` could be modified as follows:

```json
    "version":                 "2.0.0",

    "include":                 [
                                   "example3B.json",
                                   "example3C.json"
                               ],

```

In this case, `example3A.json` will inherit configuration properties from both `example3B.json` and `example3C.json`.

You can list any number of included files.

If multiple files are included, their priority order will be the order they are listed in. In this case, any properties from `example3B.json` (including all its nested included files) will take priority over any properties from `example3C.json` (including all its nested included files).

You can flag any of the included files as optional. For example:

```json
    "version":                 "2.0.0",

    "include":                 [
                                   {"value":"example3B.json", "optional":true},
                                   "example3C.json"
                               ],

```

> [!NOTE]
> Your configuration file must have a minimum `version` of `2.0.0` to use multiple includes.

## Adjust how configuration properties behave

Some configuration properties have *attributes* which affect their behaviour. Each attribute is a name : value pair.

In most cases, the default behaviour of configuration properties should be suitable. However, if you want to adjust how they behave, you can do that by changing their attributes.

For example, the configuration property `parameters.test.path` has an attribute `optional` with the data type *boolean*. You could set this attribute to `true` by modifying the configuration file as follows:

```json
{
    "version":                 "2.1.0",

    "parameters.test.path":    {"value": "MyParametersFolder/myTestFile.db", "optional": true}
}

```

All attributes are optional and are not required. If you don't set some attributes, they will revert to their default values.

For further information on the `optional` attribute, see [Configure locations for parameter files](../configure-amcore/understand-parameters.md#configure-locations-for-parameter-files). For a list of all available attributes, refer to the [Configuration property reference](../reference/configuration-property-reference.md#configuration-property-reference).

> [!NOTE]
> Your configuration file must have a minimum `version` of `2.1.0` to use attributes.

## When AMCore is offline

Some AMCore tools may be used while AMCore itself is not running, and may thus read some configuration properties while AMCore is offline. In this case, all properties will retain their values from the last AMCore session.

For example, AMCore's Diagnostic Tool is used to gather and package files into a diagnostic bundle, which may be sent back to ANCA Motion for analysis. When Diagnostic Tool runs, it reads properties of the form `parameters.*.path` , which specify user-configured locations for parameter files - and then copies these parameter files from their configured locations into its diagnostic bundle (along with various other files).

However, Diagnostic Tool is a standalone tool that may be run when AMCore is offline. In this case, the properties `parameters.*.path` will retain their values from the last AMCore session, so Diagnostic Tool will capture parameter files from their last configured locations.

> [!WARNING]
> If AMCore has been installed but has never been started, all configuration properties will be undefined. AMCore's standalone tools will thus be unable to read these properties, and may not function normally.
> For example, if Diagnostic Tool is run when AMCore has never been started, the properties `parameters.*.path` will be undefined, so Diagnostic Tool will be unable to capture any parameter files from user-configured locations.