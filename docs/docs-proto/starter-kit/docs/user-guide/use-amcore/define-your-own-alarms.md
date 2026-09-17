# Define your own alarms

You can raise your own alarms after defining them in the alarm system.

Alarm definition can take place in different places, including your part program, PLC program, or your own applications. See the respective documentation for more details about alarm interactions in different platforms:

* Part Programmer's Reference for EPPL.
* PLC Reference.
* SDK documentation for the C APIs.

## Defining your alarms

Alarm definition is written in the JSON format and can be spread over multiple files. However, you must follow the schema below:

```json
{
  // Alarm Number is Foo101
  "Foo101.enduring": false,                      
  "Foo101.enabled": true,                    
  "Foo101.suppressed": false,                 
  "Foo101.requires_confirmation": false,      
  "Foo101.latching": false,   
  "Foo101.max_time_shelved": 480,
  "Foo101.allows_suppress": true,               
  "Foo101.allows_out_of_service": true,           
  "Foo101.allows_enable": true,               
  "Foo101.acknowledgements": [ "ok", "clear" ],
  
  // Configuration for Foo102.
  "Foo102.enduring": true,
  // other properties ...
}
```

The following table lists all possible configuration properties and their details:

| Property              | Meaning                                                               | Data type        | Default value                                             |
| --------------------- | --------------------------------------------------------------------- | ---------------- | --------------------------------------------------------- |
| enduring              | Whether the alarm is enduring or transient.                           | Boolean          | false                                                     |
| enabled               | Whether the alarm is enabled when first loaded.                       | Boolean          | false                                                     |
| suppressed            | Whether the alarm is suppressed when first loaded.                    | Boolean          | false                                                     |
| requires_confirmation | Whether the alarm requires confirmation to be cleared.                | Boolean          | false                                                     |
| latching              | Whether an *enduring* alarm is latching.                              | Boolean          | false                                                     |
| max_time_shelved      | Maximum time period for which an alarm can be shelved (in *minutes*). | Unsigned Integer | 0 - alarm is unshelvable.                                 |
| allows_suppress       | Whether the suppressed state can be changed at runtime.               | Boolean          | false                                                     |
| allows_out_of_service | Whether the out-of-service state can be changed at runtime.           | Boolean          | false                                                     |
| allows_enable         | Whether the enabled state can be changed at runtime.                  | Boolean          | false                                                     |
| acknowledgements      | List of possible acknowledgements that can clear an alarm.            | Array of string  | empty array - alarm does not require any acknowledgement. |

If an alarm definition file contains invalid values such as invalid data types or duplicate keys, the entire configuration file is rejected. 

If you wish to define a latching alarm (by setting `latching` to `True`), you must also set `enduring` to `True`, otherwise the configuration becomes invalid and is rejected.

## Defining your alarm resources

### Resource files 

You can configure resources in a co-located `.resx` file. Co-located in this context means that the resource file is located within the same directory as the configuration file and carries the same file name, optionally appended with the locale name. 

For instance, if the configuration file is named Foo.json, name the resource files `Foo.de.resx`, `Foo.es.resx` and `Foo.resx` to define resources in the German, Spanish, and Invariant locales, respectively.

You can distribute resource definitions across multiple `.resx` files if necessary.

### Resource format

To define resources, write their names in the `<alarm_number>.<property>` format.

| Name             | Value           | Comment                                 |
|------------------|-----------------|-----------------------------------------|
| TEST001.message  | My first alarm  | "TEST001" is the alarm number.          |
| TEST002.message  | My second alarm | "TEST002" is the alarm number.          |

The only standard property is `message`. Other properties are considered to be optional user-defined metadata.

> [!NOTE]
> Only resources corresponding to alarms defined in the configuration file will be loaded. 
Alarms without associated resources will assume a default or blank value.