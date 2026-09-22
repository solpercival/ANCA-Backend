# What is AMCore?

*AMCore* is a flexible, high-performance software solution for controlling the motion of machines. It is the heart of the ANCA Motion CNC solution, which has been refined over 40 years.

AMCore's motion controller runs on the CNC's real-time operating system (alongside Windows) to achieve precise timing, allowing quick, deterministic responses to critical machine operations. It is able to control up to 48 axes and 10 spindles, executing up to 5000 NC instructions per second in up to 3 simultaneous part programs.

It accepts standards-compliant G-code, including all primary G-code commands such as arcs, circles and helices. It also accepts EPPL (Extended Part Programming Language), which is ANCA Motion's extension to G-code.

EPPL adds many features, including:

* Mnemonic names for G-codes
* Variables, if statements, for loops
* Spline interpolation
* User input and output prompts
* File operations

AMCore provides acceleration planning and jerk limiting using look-ahead. This means the controller will look at future commands and plan its velocities and accelerations to deliver smooth, jerk-limited motion. Look-ahead synergises with configurable path smoothing to achieve the best possible speed while preserving quality.

The patented MPG feed feature allows the execution of a part program to be controlled manually and intuitively. The retrace and active program edit features allow correction of part programs immediately during a dry-run without the need to restart. Soft axes allow complex axis combinations to be programmed as a single virtual axis.

AMCore has the following extension points:

* A PLC compiler is included, so anyone can write PLC code that AMCore compiles and executes.
* The CNC Connect API allows interaction with programs, parameters and variables from a C, C++, C# or VB.NET application.
* The OPC UA server allows interaction with variables from an OPC UA client.