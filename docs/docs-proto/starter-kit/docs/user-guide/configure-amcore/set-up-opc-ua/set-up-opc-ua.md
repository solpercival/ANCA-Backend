# Set up OPC UA

This section helps you get AMCore's OPC UA server up and running.

## Enable OPC UA

By default, the OPC UA server is not enabled. It also requires a valid certificate to start.

> [!WARNING]
> The OPC UA server feature must also have been enabled during [installation](../../get-started/install-amcore.md#install-amcore).

Set the configuration property `opcua.enable` to `true` to enable the OPC UA server.

You can either manually provide a certificate (recommended), or automatically generate one. Once you have enabled the server and provided a valid certificate, the OPC UA server starts and stops with AMCore.

### Manually provide a certificate

To manually provide a certificate:

1. Get a certificate. You can generate one via standard certificate generation software, or request a certificate from your IT administrator.  
> [!NOTE]
> The certificate must match the server configuration.
2. Add the certificate to the `LocalMachine\My` Windows Certificate Store.
3. Copy the public key certificate to:
  
```
C:\ProgramData\ANCA Motion\UA\CertificateStores\UA Applications\certs\
```
The public key certificate should be in DER format (so the file should have a .der extension).

4. Provide the certificate by setting the `opcua.certificate.subject` configuration property to the subject of the certificate.

### Automatically generate a certificate

Alternatively, you can automatically generate a certificate, allowing you to quickly get the server up and running for testing and commissioning purposes.

To do this:

1. Enable certificate generation by setting the configuration property `opcua.certificate.autogenerate` to `true`.
2. Set `opcua.certificate.validMonths` to the desired expiry of the certificate (in number of months).  

Now, the next time the OPC UA server starts, it will generate a self-signed certificate and add it to the Windows Certificate Stores.

> [!NOTE]
> The certificate will be generated to work with the configuration of the OPC UA server at the time of generation. If you further configure the server, you may need to regenerate the certificate.

## Connect to OPC UA

You'll need to connect to the OPC UA server via your OPC UA client. Refer to the documentation of your specific client to find out how to add a server.

When you're adding the server, you'll need to provide these details:

|     |     |
| --- | --- |
| Name | `ANCA Motion AMCore OPC UA Server` |
| Endpoint Url | `opc.tcp://<localhost>:51210/amcore` |

Where `<localhost>` is replaced by the name of the computer that is running AMCore (and the server).

### Accept your client certificate

The first time you connect your OPC UA client to AMCore's OPC UA server, the client certificate will be rejected and the connection will therefore fail.

Rejected certificates are placed in:

```
C:\ProgramData\ANCA Motion\UA\CertificateStores\Rejected Certificates\certs
```

Trusted certificates are placed in:

```
C:\ProgramData\ANCA Motion\UA\CertificateStores\UA Applications\certs
```

To accept your client certificate, simply move it from the rejected directory into the trusted directory.

### Browse the address space

Once you're connected, you should be able to see there are a few default nodes in the Objects folder that you can browse. These are:

| Namespace | Node | Description | Node Id | Sample Value |
| --- | --- | --- | --- | --- |
| [http://opcfoundation.org/UA/](http://opcfoundation.org/UA/) | Server | Collection of nodes that are part of the OPC UA standard. | `2253` | \-  |
| urn:ancamotion:amcore | System | A folder node that contains the default AMCore variable nodes. | `{fe9ffde4-27cc-44d9-9bad-1af464c14063}` | \-  |
| urn:ancamotion:amcore | AMCore File Version | A string representation of the file version of AMCore that is running. | `{e2054d06-264c-4d05-90e8-656fee5ecdda}` | 1.8.211.0 |
| urn:ancamotion:amcore | AMCore Product Version | A string representation of the product version of AMCore that is running. | `{0e2cb1fb-18fd-4254-86e3-ac140f7ce4a3}` | 1.8.0 |
| urn:ancamotion:amcore | PMK Version | A string representation of the installed PMK version. | `{246dae8b-33dd-43b8-a26e-cf80bb112573}` | SW646-0-00-6000 |

Next steps

For most applications, the default nodes in the address space won't be enough to do anything useful. Continue to [Configure the address space](configure-the-address-space.md#configure-the-address-space) to add your own nodes to the server.