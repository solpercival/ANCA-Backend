# am-license

If an internet connection is not available on the target system, it is necessary to use a tool to prepare and license the software locally. Your system may provide a suitable tool especially suited to your needs (please refer to relevant documentation accompanying the tool), otherwise, a command line tool called `am-license` is available for offline scenarios.

> [!TIP]
> `am-license` is typically located at `%amcore_home%\3dx\bin\licensing`

Commands follow the format:

`am-license [*OPTION*]...`

| **Parameter**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; | **Description** |
| --- | --- |
| `-i, --information` | Output information about locally available licenses to the command prompt. |
| `-c, --create-container` | Creates a software container on the local system. |
| `-x, --create-context=PATH` | Write information about the local software container to the file specified by PATH. This file is referred to as a context file and is required for offline activation of a license. If a container does not already exist on the local system, one will be created. Use in combination with the `--serial-number` option if more than one container exists on the local system. |
| `-s, --serial-number=SERIAL` | Use in combination with other options to specify a single container if more than one container exists on the local system. |
| `-u, --update-license=PATH` | Updates a local license with the update file specified by PATH. |
| `-t, --update-time` | Synchronize the timestamp of all local containers with the certified time server (requires internet connection). Use in combination with the `--serial-number` option to update the timestamp of a single container only. |
| `-h, -?, --help` | Output this usage information to the command prompt. |

> [!WARNING]
> The following sample syntax assumes the current directory is the directory containing `am-license.exe`

> [!CAUTION]
> Some early versions of `am-license` do not support environment variables being passed as arguments (e.g. `%UserProfile%` in the samples below). If you get a message indicating that the operation failed when using an environment variable, please try again with the environment variable expanded.

Sample syntax to create a context file on the desktop using console:

```console
am-license --create-context="%UserProfile%\Desktop\context.WibuCmRaC"
```

If there are multiple containers found on the target system, you need to specify the serial number of the container as well. Use the command as given below in such case:

```console
am-license --serial-number=SERIAL --create-context="%UserProfile%\Desktop\context.WibuCmRaC"
```

Sample syntax to update a local license with a provided update file `xxx-xxxxxxxxxx.WibuCmRaU` located on the desktop:

```console
am-license --update-license="%UserProfile%\Desktop\xxx-xxxxxxxxxx.WibuCmRaU"
```

See also

- [Activate your license](../get-started/activate-your-license.md#activate-your-license)