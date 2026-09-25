# Install AMCore

This section describes how to install AMCore via the Windows desktop or via the command line (allows silent unattended installs).

## Install via Windows desktop

1. Double-click the installer file to start the installation process.
2. Click **Next**.
3. After agreeing to the license terms, click **Next**.
4. (*Optional*) Enable the SDK if you want to develop applications that interface with AMCore.
5. (*Optional*) Enable the OPC UA Server if you want to interface with AMCore using the OPC UA protocol.
6. Click **Install**.

## Install via command line

Installing AMCore via the command line allows you to install, repair, or uninstall silently. To install AMCore via the command line use Microsoft's [Msiexec utility.](https://learn.microsoft.com/en-us/windows/win32/msi/command-line-options)

> [!WARNING]
> Make sure you have administrator rights if installing via the command line.


Use the `/qn` option to install without showing the installer graphical interface. Select features using `ADDLOCAL`.

For example, below is sample syntax to silently install AMCore, the SDK and the OPC UA server:

```console
msiexec /i AMCore-PCC-2.0.0.msi /qn ADDLOCAL=Core,SDK,OpcUaServer
```

## Change versions

The **minor version** of AMCore is the second number in the version. The **patch number** is the third. For example, AMCore 2.1.0 has a minor version number of 1 and a patch number of 0.

### Change minor version

AMCore supports **side-by-side installations** of minor versions. So, you can have AMCore 2.0 installed at the same time as AMCore 2.1.

To install another minor version, simply follow the usual installation steps. The existing minor version can be removed as required.

If you wish to keep both versions installed, you can select which version to run using the `-version` option in the [AMCore command line interface](./start-amcore.md#command-line-interface).

### Change patch version

Where `x` is the minor version number of AMCore you wish to use.

To upgrade from a previous version of AMCore with the same minor version number, simply follow the usual installation steps.

To downgrade, you must first uninstall the previous AMCore version before installing as usual.