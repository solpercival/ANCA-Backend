# Configure the address space

Now you've got the OPC UA server up and running, you'll want to configure the address space so that you can access the appropriate data from a client.

This section guides you through the process of creating a nodeset file with one of each type of supported node. Repeat or skip portions to configure the server to suit your needs.

## Prerequisites

Before continuing through this section, make sure you've completed the steps in [Set up OPC UA](set-up-opc-ua.md#set-up-opc-ua). In particular, you should be able to start the OPC UA server and connect to it from a client.

## Provide a nodeset

The address space of the OPC UA server is configured by providing a *nodeset*, which is an XML representation of the address space.

> [!NOTE]
> Learn more about the OPC UA information model XML schema in the online [OPC UA Online Reference](https://reference.opcfoundation.org/v104/Core/docs/Part6/F.1/).

To provide a nodeset:

1. Create an XML file with the following contents:

```xml
<?xml version="1.0" encoding="utf-8"?>
<UANodeSet xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns="http://opcfoundation.org/UA/2011/03/UANodeSet.xsd">
  <NamespaceUris>
    <Uri>sample:uri</Uri>
  </NamespaceUris>
  <Aliases>
    <Alias Alias="Organizes">i=35</Alias>
    <Alias Alias="HasTypeDefinition">i=40</Alias>
  </Aliases>
</UANodeSet>
```

2. Provide the nodeset to AMCore by setting the `opcua.nodeset.path` configuration property to the path to the file you create in (1).

This simple nodeset adds a namespace with URI `sample:uri` to the server. You can add other namespaces by adding more `Uri` elements. The `Aliases` element allows you to substitute a string for commonly used identifiers, making the nodeset more readable. The sample above contains two simple aliases that will be useful later.

## Add a variable node

An OPC UA variable node can be added to the server to represent an AMCore variable node. To add a variable node for the `G_CORE_RUNNING` AMCore variable:

1. Add the following lines to the nodeset after the `Aliases` element:

```xml
  <UAVariable NodeId="ns=1;s=SampleVariable" BrowseName="SampleVariable" MinimumSamplingInterval="5000">
    <DisplayName Locale="en">Sample Variable</DisplayName>
    <Description Locale="en">A sample boolean value indicating whether the AMCore system is running.</Description>
    <References>
      <Reference ReferenceType="HasTypeDefinition">i=63</Reference>
      <Reference ReferenceType="Organizes" IsForward="false">i=85</Reference>
    </References>
    <Extensions>
      <Extension>
        <GeneratedNode xsi:type="Variable" xmlns="http://schemas.ancamotion.com/opcua/2020/09">
          <Name>(CNC)G_CORE_RUNNING</Name>
        </GeneratedNode>
      </Extension>
    </Extensions>
  </UAVariable>
```

2. Restart AMCore. Connect to the OPC UA server from your client and confirm that the variable node is present.

For the node identifier (`NodeId`), the first part (`ns=1`) determines the namespace of the node. The number is a 1-based index into the list of namespace URIs in the `NamespaceUris` element; the namespace index of the node in the server will be different. The second part (`s=SampleCoreRunning`) defines the type of the identifier as a string (`s=`) and sets it to "SampleCoreRunning". You can also use `g=` for a GUID identifier or `i=` for an numeric (unsigned 16-bit integer) identifier.

> [!TIP]
> So, to add a another variable node, duplicate this section in your nodeset and change the `NodeId` and the `Name` of the variable. You can also change the `BrowseName`, `MinimumSamplingInterval`, `DisplayName`, `Description` and `References` (but keep the type definition reference) as you see fit.

The `References` element adds references to the node. For this node, the first reference places the node in the "Objects" folder (`i=85`) and second reference defines it as a "BaseDataVariableType" (`i=63`). Hopefully you can see how the aliases have improved the readability of the reference types.

The extensions portion of the XML causes the server to retrieve/create the AMCore node for the variable (when retrieving, the value of the `Name` element must match the name of the AMCore variable) and link it to the node. 

> [!TIP]
> You can also add variable nodes to the server by simply adding them to AMCore using CNC Connect (see the the **Node Functions** section of the CNC Connect API Reference). They will automatically appear in the OPC UA server with the root AMCore nodes appearing under the Objects folder with an "Organizes" reference.
> If a node identifier for an AMCore node conflicts with an OPC UA node, the AMCore node will override the OPC UA node.

## Add a file node

A file node represents a file on the file system of the system running the server.

> [!NOTE]
> Learn more about file nodes in the [OPC UA Online Reference](https://reference.opcfoundation.org/v104/Core/docs/Part5/C.2.1/).

To add a file node to the server:

1. Create an empty text file at the following location: `%UserProfile%\Documents\OPC UA Samples\Sample File.txt` 
2. Add the following lines to the nodeset after the variable node:

```xml
  <UAObject NodeId="ns=1;s=SampleFile" BrowseName="SampleFile">
    <DisplayName Locale="en">Sample File</DisplayName>
    <Description Locale="en">A sample text file.</Description>
    <References>
      <Reference ReferenceType="HasTypeDefinition">i=11575</Reference>
      <Reference ReferenceType="Organizes" IsForward="false">i=85</Reference>
    </References>
    <Extensions>
      <Extension>
        <GeneratedNode xsi:type="File" xmlns="http://schemas.ancamotion.com/opcua/2020/09">
          <Path>%UserProfile%\Documents\OPC UA Samples\Sample File.txt</Path>
        </GeneratedNode>
      </Extension>
    </Extensions>
  </UAObject>
```

3. Restart AMCore. Connect to the OPC UA server from your client and confirm that the file node is present.

There's a few things to note about this section of the nodeset:

- The `NodeId` has changed. This is because all node identifiers in the server must be unique.
- The "TypeDefinition" has changed to `i=11575`. If you browse the types in the server, you'll see this is the identifier for the "FileType" node.
- The extensions now describe a file node (`xsi:type="File"`) and the `Path` element points to the file on disk.

> [!TIP]
> So, to add another file node, duplicate this section in your nodeset and change the `NodeId` and the `Path` to the file. You can also change the `BrowseName`, `DisplayName`, `Description` and `References` (but keep the type definition reference) as you see fit.
> Alternatively, place all the files you like into a dedicated directory and add a file directory node instead.

# Add a file directory node

A file directory node represents a file directory on the file system of the system running the server.

> [!NOTE]
> Learn more about file directory nodes in the [OPC UA Online Reference](https://reference.opcfoundation.org/v104/Core/docs/Part5/C.3.1/).

To add a file directory node to the server:

1. Create an folder named `Sample File Directory` in the following location: `%UserProfile%\Documents\OPC UA Samples\`
2. Add any files or folders you'd like to appear in the server to the folder.
3. Add the following lines to the nodeset after the file node:

```xml
  <UAObject NodeId="ns=1;s=SampleFileDirectory" BrowseName="FileSystem">
    <DisplayName Locale="en">Sample File Directory</DisplayName>
    <Description Locale="en">A sample file directory.</Description>
    <References>
      <Reference ReferenceType="HasTypeDefinition">i=13353</Reference>
      <Reference ReferenceType="Organizes" IsForward="false">i=85</Reference>
    </References>
    <Extensions>
      <Extension>
        <GeneratedNode xsi:type="FileDirectory" xmlns="http://schemas.ancamotion.com/opcua/2020/09">
          <Path>%UserProfile%\Documents\OPC UA Samples\Sample File Directory\</Path>
        </GeneratedNode>
      </Extension>
    </Extensions>
  </UAObject>
```

4. Restart AMCore. Connect to the OPC UA server from your client and confirm that the file directory node is present.

Note:

- The type definition is now `i=13353` which is the node identifier for the "FileDirectoryType" node.
- The extensions now describe a file directory node.

> [!TIP]
> So, to add another file directory node, duplicate this section in your nodeset and change the `NodeId` and the `Path` to the file directory. You can also change the `BrowseName`, `DisplayName`, `Description` and `References` (but keep the type definition reference) as you see fit.

## Add a folder node

A folder node is a simple type of node that is only used to organize other nodes.

To add a folder node that organizes the nodes that we added above:

1. Add the following lines to the nodeset above the variable node:

```xml
  <UAObject NodeId="ns=1;s=SampleFolder" BrowseName="SampleFolder">
    <DisplayName Locale="en">Samples</DisplayName>
    <Description Locale="en">A folder that contains sample nodes.</Description>
    <References>
      <Reference ReferenceType="HasTypeDefinition">i=61</Reference>
      <Reference ReferenceType="Organizes" IsForward="false">i=85</Reference>
    </References>
  </UAObject>
```

2. Change the "Organizes" references for each of the other nodes to:
```
      <Reference ReferenceType="Organizes" IsForward="false">ns=1;s=SampleFolder</Reference>
```
3. Restart AMCore. Connect to the OPC UA server from your client and confirm that the folder node is present. The 3 nodes we made earlier should be nested under the folder.

As you may have noticed, the references for a node can be either "forward" (`IsForward="true"`) or "reverse" (`IsForward="false"`). For "Organizes" references, a forward reference means that the node organizes another node and a reverse reference means that the node is organized by another node.

So, instead of adding reverse organizes references for each node, we could have added a forward organizes reference for each of the nodes to the folder node instead. Of course, adding both the forward and reverse references is completely fine, too.

## Next steps

If you've followed the steps exactly, your XML file should look like this:

**SampleNodeset.xml** Expand source

```xml
<?xml version="1.0" encoding="utf-8"?>
<UANodeSet xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns="http://opcfoundation.org/UA/2011/03/UANodeSet.xsd">
  <NamespaceUris>
    <Uri>sample:uri</Uri>
  </NamespaceUris>
  <Aliases>
    <Alias Alias="Organizes">i=35</Alias>
    <Alias Alias="HasTypeDefinition">i=40</Alias>
  </Aliases>
  <UAObject NodeId="ns=1;s=SampleFolder" BrowseName="SampleFolder">
    <DisplayName Locale="en">Samples</DisplayName>
    <Description Locale="en">A folder that contains sample nodes.</Description>
    <References>
      <Reference ReferenceType="HasTypeDefinition">i=61</Reference>
      <Reference ReferenceType="Organizes" IsForward="false">i=85</Reference>
    </References>
  </UAObject>
  <UAVariable NodeId="ns=1;s=SampleVariable" BrowseName="SampleVariable" MinimumSamplingInterval="5000">
    <DisplayName Locale="en">Sample Variable</DisplayName>
    <Description Locale="en">A sample boolean value indicating whether the AMCore system is running.</Description>
    <References>
      <Reference ReferenceType="HasTypeDefinition">i=63</Reference>
      <Reference ReferenceType="Organizes" IsForward="false">ns=1;s=SampleFolder</Reference>
    </References>
    <Extensions>
      <Extension>
        <GeneratedNode xsi:type="Variable" xmlns="http://schemas.ancamotion.com/opcua/2020/09">
          <Name>(CNC)G_CORE_RUNNING</Name>
        </GeneratedNode>
      </Extension>
    </Extensions>
  </UAVariable>
  <UAObject NodeId="ns=1;s=SampleFile" BrowseName="SampleFile">
    <DisplayName Locale="en">Sample File</DisplayName>
    <Description Locale="en">A sample text file.</Description>
    <References>
      <Reference ReferenceType="HasTypeDefinition">i=11575</Reference>
      <Reference ReferenceType="Organizes" IsForward="false">ns=1;s=SampleFolder</Reference>
    </References>
    <Extensions>
      <Extension>
        <GeneratedNode xsi:type="File" xmlns="http://schemas.ancamotion.com/opcua/2020/09">
          <Path>%UserProfile%\Documents\OPC UA Samples\Sample File.txt</Path>
        </GeneratedNode>
      </Extension>
    </Extensions>
  </UAObject>
  <UAObject NodeId="ns=1;s=SampleFileDirectory" BrowseName="FileSystem">
    <DisplayName Locale="en">Sample File Directory</DisplayName>
    <Description Locale="en">A sample file directory.</Description>
    <References>
      <Reference ReferenceType="HasTypeDefinition">i=13353</Reference>
      <Reference ReferenceType="Organizes" IsForward="false">ns=1;s=SampleFolder</Reference>
    </References>
    <Extensions>
      <Extension>
        <GeneratedNode xsi:type="FileDirectory" xmlns="http://schemas.ancamotion.com/opcua/2020/09">
          <Path>%UserProfile%\Documents\OPC UA Samples\Sample File Directory\</Path>
        </GeneratedNode>
      </Extension>
    </Extensions>
  </UAObject>
</UANodeSet>
```

Repeat any of the above steps as required to finish configuring the OPC UA server. Once you're done, continue [configuring AMCore](../configure-amcore.md#configure-amcore), or start [using it](../../use-amcore/use-amcore.md#use-amcore).