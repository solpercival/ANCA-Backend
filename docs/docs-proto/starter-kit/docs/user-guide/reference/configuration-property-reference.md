# Configuration property reference

You can configure AMCore by providing a *configuration file* containing some *configuration properties*, which are settings that apply to the current AMCore session. See [Understand configuration properties](../configure-amcore/understand-configuration-properties.md#understand-configuration-properties) for details.

A configuration file is in JSON format and contains one or more configuration properties. Each configuration property is a name : value pair. Configuration properties are of 5 basic types: *boolean*, *integer*, *floating-point*, *string* or *array of strings*.

The following tables list all AMCore configuration properties. You can provide a configuration file containing some or all of these properties.

All configuration properties are optional. If you don't set (or inherit) some properties, they will revert to their default values.

File and folder locations may be specified using absolute or relative paths. Environment variables may be used. Folders should be delimited with forward slashes `/`.

You can adjust how configuration properties behave by changing their *[attributes](#attributes)*. See [Adjust how configuration properties behave](../configure-amcore/understand-configuration-properties.md#adjust-how-configuration-properties-behave) for details.

A configuration file may include *[special entries](#special-entries)* alongside its configuration properties:

- `version` should be used to specify the file format. The original file format is `1.0.0` and the latest is `2.1.0`.  
Where a minimum `version` is listed (below), that feature can only be used in configuration files whose `version` is equal to or higher than the minimum.  
Where no minimum `version` is listed, that feature can be used in configuration files with any valid `version`.
- `include` may be used to inherit configuration properties from nested configuration files.

## Parameters

These configuration properties specify custom locations for *parameter files*, which contain *[parameters](../configure-amcore/understand-parameters.md#understand-parameters)* to configure AMCore. The parameter files have a fixed priority order as listed here.

If you customise the location of a parameter file, the file must exist in that location. However, you can change this behaviour via the `optional` *[attributes](#attributes)*.

| Name | Type | Default (legacy) location | Units | Description |
| --- | --- | --- | --- | --- |
| `parameters.test.path` | `String` | `<home folder>\misc\p_test.db` | `-` | Path of the *test* parameter file. |
| `parameters.user.path` | `String` | `<home folder>\misc\p_user.db` | `-` | Path of the *user* parameter file. |
| `parameters.oem.path` | `String` | `<home folder>\misc\p_oem.db` | `-` | Path of the *oem* parameter file. |
| `parameters.mspec.path` | `String` | `<home folder>\db\config\p_mspec.db` | `-` | Path of the *mspec* parameter file. |
| `parameters.common.path` | `String` | `<home folder>\db\config\p_common.db` | `` `-` `` | Path of the *common* parameter file. |

## Programs

| Name | Type | Default | Units | Description |
| --- | --- | --- | --- | --- |
| `programs.paths` | `Array of strings` | `[]` | `-` | Part program search hierarchy.<br><br>This is an ordered list of folder paths, in which AMCore will search for part programs. If a folder doesn't exist, it is skipped. |

## OPC UA

| Name and Type | Default | Description |
| --- | --- | --- |
| `opcua.enable`<br>**Type:** `Boolean` | `false` | Whether the OPC UA server is enabled.<br><br>Set to `true` to enable the server. |
| `opcua.applicationUri`<br>**Type:** `String` | `urn:localhost:ancamotion:`<br>`amcore` | Application instance URI of the OPC UA server.<br><br>This value uniquely identifies the server and should match the URL value in the certificate subject alternative name. Note that the OPC UA server will automatically convert `localhost` to the host name. |
| `opcua.certificate.`<br>`autogenerate`<br>**Type:** `Boolean` | `false` | Whether to automatically generate a certificate.<br><br>Set to `false` if you are providing your own certificate.<br><br>Set to `true` to have AMCore automatically generate a self-signed certificate. The lifetime of this certificate is specified via `opcua.certificate.validMonths`. |
| `opcua.certificate.subject`<br>**Type:** `String` | `CN=ANCA Motion AMCore`<br>`OPC UA Server` | Subject field of certificate.<br><br>This value must match the subject field of the certificate. |
| `opcua.certificate.validMonths`<br>**Type:** `Integer` | `0` | Lifetime of automatically generated certificate.<br><br>The number of months for which the generated certificate is valid. |
| `opcua.nodeset.path`<br>**Type:** `String` | `-` | Path of the nodeset file, which initializes the address space of the server. |

## Tools

| Name | Default (legacy) location | Description |
| --- | --- | --- |
| `tools.backup.configuration.path`<br>**Type:** `String` | `<home folder>\misc\user_backup_list.txt` | Path of a configuration file for the User Backup tool.<br><br>Configuration file contains a list of paths to backup. |

## Attributes

You can adjust how configuration properties behave by changing their *attributes*. Each attribute is a name : value pair.

The following table lists all attributes and the configuration properties they apply to. Configuration properties that are not listed have no attributes.

All attributes are optional and are not required. If you don't set some attributes, they will revert to their default values.

| Attribute | Type | Default | Applies to configuration properties | Description |
| --- | --- | --- | --- | --- |
| `optional` | `Boolean` | `false` | `parameters.*.path` | Whether the parameter file is optional.<br><br>If `false`, the file must exist in its custom location.<br><br>If `true`, the file will be ignored if it doesn't exist.<br><br>See [Configure locations for parameter files](../configure-amcore/understand-parameters.md#configure-locations-for-parameter-files) for details. |

> [!NOTE]
> Your configuration file must have a minimum `version` of `2.1.0` to use attributes.

## Special Entries

A configuration file may include these *special entries* alongside its configuration properties.

| Name | Type | Default | Units | Description |
| --- | --- | --- | --- | --- |
| `version` | `String` | `1.0.0` | `-` | Semantic version string specifying the configuration file format.<br><br>Should be included in every configuration file. The original file format is `1.0.0` and the latest is `2.1.0`. |
| `include` | `String`<br>OR `Object`<br>OR `Array` | `-` | `-` | Included configuration file(s), to inherit any configuration properties from those file(s).<br><br>May be one of the following:<br><br>- To include a single file (*string* type):  <br>`"include": <path>`<br>- To include a single file, and optionally flag it as optional (*object* type):  <br>`"include": {"value":<path>, "optional":<opt>}`<br>- To include multiple files (*array* type):  <br>`"include": [<include file>, <include file>, ...]`<br><br>where:<br><br>- `<path>` (*string*) is the path of the included file<br>- `<opt>` (*boolean*) specifies whether the included file is optional. If `false` (or omitted), the file must exist. If `true`, the file will be ignored if it doesn't exist.<br>- each `<include file>` may be either `<path>` (*string* type) or `{"value":<path>, "optional":<opt>}` (*object* type).<br><br>Your properties (in your configuration file) will take priority over any included properties (from any included files). If multiple files are included, their priority order will be the order they are listed in. Any properties from the 1st included file (including all its nested included files) will take priority over any properties from the 2nd included file (including all its nested included files), and so on.<br><br> NOTE - Your configuration file must have a minimum `version` of `2.0.0` to use optional includes or multiple includes. |