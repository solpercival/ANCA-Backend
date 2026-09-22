# Set up your environment

As its name suggests, AMCore contains the core functionality of a complete motion control solution. This means additional files and configuration are required to get the system up and running.

In particular, you should provide:

* The locations of your files
* Custom PLC
* Parameter files
* (*Optional*) A user interface
* (*Optional*) A launcher

## Set up the reference project

Before you continue, make sure you've completed the setup instructions provided with the reference project.

## Understand the reference project

Once you've set up the reference project, you'll be ready to go.

Before you continue with the next section, you should make sure you understand each of the components of the project and how they are integrated into AMCore. The rest of this section is dedicated to this.

### Home folder

The home folder is the default folder used when a path is not configured. It is the combination of a registry entry and an environment variable.

The registry entry value is an absolute path to a common folder, which is commonly referred to as the "OEM path". The key for it is (for 64-bit systems):

```
HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\ANCA\OEM\OemPATH
```

The environment variable value is the name of the final folder. It is defined by the environment variable "Target". Don't change it unless you know what you're doing.

### Configuration

AMCore is configured via parameters. The reference project contains parameter files to set AMCore up as a simulator.

AMCore knows where these files are via configuration properties. In particular, the reference project includes a configuration file containing configuration properties that define the locations of these files. This configuration file is passed to AMCore by the launcher.

> [!NOTE]
> For more information, look at the [Understand parameters](../configure-amcore/understand-parameters.md) and [Understand configuration properties](../configure-amcore/understand-configuration-properties.md#understand-configuration-properties) concepts.


### Programmable logic controller

PLC is an essential component of AMCore. There is a base level of functionality included with the reference project, but you can extend this if you like. For more information, refer to the PLC Programmers Reference.

AMCore knows the location of the PLC files via parameters.

### User interface

The reference project contains a sample user interface to command AMCore. This is achieved through the AMCore API: CNC Connect. You can learn more about CNC Connect in the CNC Connect API.

The user interface is run by the launcher.

### Launcher

Finally, the reference project contains a simple launcher that:

* Launches AMCore, passing the configuration file
* Launches the user interface, exposing some simple machine commands