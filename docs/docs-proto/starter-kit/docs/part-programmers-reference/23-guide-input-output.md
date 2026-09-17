# Input and Output

The input and output (I/O) commands let a part program accept input from the operator, a text file or a device, display information in windows, write data to files or devices, and manage the streams that carry that data. Output is performed by the `write` function; input is performed by the `readkey` and `read` functions. These commands are sometimes called Interactive Conversational Programming (ICP) functions; the AMCore CNC does not require a special mode to use them, and they may be included in normal EPPL programs.

**Commands and Variables**

| Name                                         | Type     | Description                                                            |
| -------------------------------------------- | -------- | ---------------------------------------------------------------------- |
| [`close`](./05-functions.md#close)           | function | Closes a file stream previously opened with `open`.                    |
| [`fdelete`](./05-functions.md#fdelete)       | function | Deletes a file; wildcard characters are accepted.                      |
| [`fexists`](./05-functions.md#fexists)       | function | Tests whether a file exists and can be accessed.                       |
| [`open`](./05-functions.md#open)             | function | Opens a file as a named stream for reading or writing.                 |
| [`read`](./05-functions.md#read)             | function | Reads a formatted field from a stream into a variable.                 |
| [`readkey`](./05-functions.md#readkey)       | function | Reads a single character from a stream into a string variable.         |
| [`sync`](./05-functions.md#sync)             | function | Synchronises lookahead with run-time state                             |
| [`wclose`](./05-functions.md#wclose)         | function | Closes the VDU window.                                                 |
| [`wopen`](./05-functions.md#wopen)           | function | Opens the VDU window.                                                  |
| [`write`](./05-functions.md#write)           | function | Writes formatted output to a stream.                                   |
| [`keyboard`](./07-constants.md#keyboard)     | constant | Predefined input stream: the operator keyboard.                        |
| [`printer`](./07-constants.md#printer)       | constant | Predefined output stream: the parallel printer port, if fitted.        |
| [`read_error`](./07-constants.md#read_error) | constant | Return code: an error occurred during the read.                        |
| [`read_ok`](./07-constants.md#read_ok)       | constant | Return code: the read completed successfully.                          |
| [`read_tmout`](./07-constants.md#read_tmout) | constant | Return code: a programmed timeout expired before a character was read. |
| [`vdu`](./07-constants.md#vdu)               | constant | Predefined output stream: the video display unit (window).             |

## Streams

A stream is the source of input data or the destination of output data. Input streams may be the keyboard, a text file or a device; output streams may be the VDU, a text file or a device. Input and output are directed from or to a stream by giving the stream name as the first argument of the `write`, `readkey` and `read` functions.

There are three predefined streams:

| Stream     | Direction | Description                       |
| ---------- | --------- | --------------------------------- |
| VDU        | Output    | Video display unit (window).      |
| `keyboard` | Input     | Operator keyboard.                |
| `printer`  | Output    | Parallel printer port, if fitted. |

If the stream name is omitted, it defaults to VDU for `write` and `keyboard` for `readkey` and `read`. The programmer may also define streams by opening files or devices with `open`; the resulting stream identifier is then used to read and write data.

File input and output occur during program lookahead, but the current run-time state is maintained: if a cancel-lookahead event occurs, all open files and their open/close states are restored to the correct run-time state.

### Window Open

When the VDU stream is used for output (the default when no stream is given) or the `keyboard` stream is used for input, output is placed in a window and input requires a lit window. A window is opened in two ways: explicitly, with the `wopen` command, or implicitly, when `write` is first called with the VDU stream or `read` or `readkey` is called with the `keyboard` stream. The programmer does not normally need to program `wopen` explicitly, unless the window must be opened before use or the default window's window handle is needed. See the `wopen` entry for details.

### Window Close

A window opened explicitly with `wopen`, or implicitly by using the VDU stream for output or the `keyboard` stream for input, may be closed explicitly with the `wclose` command. The window is also closed automatically under several conditions, though this is usually unnecessary. A window is closed automatically when the program is rewound, deactivated or on a cancel-lookahead condition. Typical cancel-lookahead conditions are a premature abort due to an error, active program editing, and a conditional move (using `stopif` or `stopifnot`) firing. See the `wclose` entry for details.

### File Open

Disk files may be opened and closed to read and write data, giving the data permanent storage. All data is written to files as ASCII text so that it is human readable. Files are opened with the `open` function, which associates a file with a named stream identifier used by later read, write and close operations. A file is opened in one of three modes: `input` (read access only), `output` (write access only, deleting any existing file first) or `append` (write access only, appending to an existing file). A file opened for writing should be closed as soon as writing is finished; all files close automatically when the part program completes, is rewound or is deactivated. See the `open` and `close` entries for the full syntax and behaviour.

### File Close

A disk file opened with `open` may be closed explicitly with the `close` function, passing the stream identifier used in the matching `open` call. Before a closed file can be read or written again it must be reopened. See the `close` entry for details.

### File Delete

The `fdelete` command deletes unwanted or temporary files. It runs quietly and does not prompt before deleting, and it will not delete a read-only file. Wildcard characters are accepted in the filename. See the `fdelete` entry for syntax and examples.

### File Exists

The `fexists` command checks whether a specified file exists and whether it can be accessed. Environment variable expansion is allowed in the filename. It returns a code distinguishing three cases: the file does not exist, exists but cannot be accessed, or exists and can be accessed. See the `fexists` entry for the return values and examples.

## Formatted Output

Text may be output to a predefined output stream (VDU or `printer`), to a disk file, or to a device opened in `append` or `output` mode, using the `write` function. The first argument may be an optional stream identifier, followed by a format string and optional trailing arguments (each corresponding to a conversion specification); if the stream is omitted, VDU is assumed. See the `write` entry for the full syntax. The format string describes the output and contains four kinds of object: ordinary characters, conversion specifications (see Conversion Specifications), escape sequences and extended modifiers, each described below.

### Ordinary Characters

Ordinary characters are any characters other than `@`, `$`, `%`, `!`, `\` and `"`. These characters are output directly.

### Escape Sequences

The backslash character `\` is an escape character used to insert escape sequences into the format string and to output characters that are otherwise reserved. The supported escape sequences are:

| Sequence | Meaning                                                           |
| -------- | ----------------------------------------------------------------- |
| `\n`     | Newline.                                                          |
| `\t`     | Horizontal tab.                                                   |
| `\l`     | Clear from the cursor to the end of the line (VDU stream only).   |
| `\s`     | Clear from the cursor to the end of the screen (VDU stream only). |
| `%%`     | Print the character `%`.                                          |
| `\!`     | Print the character `!`.                                          |
| `\\`     | Print the character `\`.                                          |
| `\"`     | Print the character `"`.                                          |

**Example:**

```
write("Line 1\nLine 2\n \"Line 3\"$\n")
```

This displays:

```
Line 1
Line 2
 "Line 3"$
```

### Write to VDU

The VDU stream is the default when no stream identifier is given; it may also be named explicitly. In addition to the conversion specifications and escape sequences, a number of extended modifiers may be included in the format string to modify the appearance of the text within the window, such as the Inch/Metric modifier described below.

**Example:**

```
write(VDU, "this is a test")
```

is identical to:

```
write("this is a test")
```

### Inch/Metric Modifier

The Inch/Metric modifier prints different text depending on the dimensioning mode of the machine, which is useful for unit labels. Its syntax is:

```
#m'metric_label'
#i'inch_label'
```

**Example:**

```
write("#i'inches'#m'mm'")
```

This writes "inches" when the machine is in inch mode and "mm" when it is in metric mode.

Inch or metric mode is determined by the state of the output logical `OLB_INCH_MODE`. If this mode has been changed recently in the program, program a `sync` before using this modifier so that the string reflects the desired state.

### Write to Text File

Once a file has been opened in `append` or `output` mode, data may be written to it by giving the stream identifier as the first argument of `write`. All data is written in ASCII text form, in the same way as VDU output, so all of the conversion specifications are valid.

**Example:**

```
{
  Open a file /tmp/data1.txt for writing, deleting it first if it exists,
  write the string Variable IV1 = 68 followed by a newline, then close the file.
}
iv1 = 23 + 45
sv1 = "/tmp/data1.txt"
open(&outdata, sv1, output)
write(outdata, "Variable IV1 = %d\n", iv1)
close(outdata)
```

## Input

Data may be input from the predefined input stream (`keyboard`), from a disk file, or from a device opened in `input` mode. The `read` function inputs formatted data; the `readkey` function inputs data one character at a time.

### Formatted Data Input

Formatted data input reads data as a string and converts it to one of the basic data types -- Boolean, integer, float or string. Input is possible from the operator via the `keyboard` stream, from a disk file, or from a device, using the `read` function. The raw input string is converted to the variable's type using the type-casting rules, so the variable's type determines the conversion; a local variable must be initialised first so that its type is known. If the stream is omitted, `keyboard` is assumed and the data is read from a field within a window on the VDU. `read` returns `read_ok` on success, `read_eof` if the end of the file was reached, or `read_error` on error; when a failure is returned the data in the variable is invalid. See the `read` entry for the full syntax.

### Single Character Input

Single character input reads data one character at a time with the `readkey` function, from the `keyboard` stream (the default), a disk file or a device. The character read is placed in a string variable. An optional timeout, in seconds, applies to input devices such as serial devices and causes a `read_tmout` error if no character arrives in time. `readkey` returns the character read on success, or `read_eof`, `read_tmout` or `read_error` on failure. See the `readkey` entry for the full syntax.

### Read from Keyboard

When `read` reads data from the keyboard, a data window is opened if it is not already open, and a data-entry box appears on the second-last line of the window. The box is initially filled with the current value of the variable passed to `read`, which the operator may re-enter or edit. The field is treated as a string entry field.

Data entry is always in insert mode. The first key pressed determines whether the existing string is edited or replaced: if it is a navigation key, the existing string is edited; otherwise the existing string is erased and the entry becomes the first character of the new string. The navigation keys are:

| Key             | Action                                                                   |
| --------------- | ------------------------------------------------------------------------ |
| Left            | Move the cursor one character to the left.                               |
| Right           | Move the cursor one character to the right.                              |
| Home            | Move the cursor to the first character in the string.                    |
| End             | Move the cursor past the last character in the string.                   |
| Delete (DEL)    | Delete the character under the cursor.                                   |
| Back space (BS) | Delete the character to the left of the cursor.                          |
| ENTER           | Accept the entered data and typecast it to the type of the variable.     |
| ESCAPE          | Reject the entered data and return to the initial value of the variable. |

When `readkey` is used to input a single keystroke, it returns immediately once a key is pressed and does not echo the character to the VDU; the programmer must display it if required.

**Additional information:**

1. `readkey` may not be used to read PLC and front-panel switches.

### Read from Text File

Data may be read from a disk text file once it has been opened in `input` mode, by giving the stream identifier as the first argument of `read` or `readkey`. For `readkey`, data is input one character at a time regardless of the formatting of the data in the file. For `read`, data is input as ASCII text -- a raw string -- and then typecast to the type of the variable. Data is read as a field: a field is data separated by white space (spaces, tabs and newlines). Each successive call to `read` collects the next field, converts it and places the result in the variable.

**Example:**

```
{
  For an input file containing:
    12 13 /tmp/xxx 103.4
    on -8.3e-4
  the following extract inputs the data into typed variables.
}
open(&indata, "/tmp/infile.dat", input)
read(indata, &iv1) { input the integer 12 }
read(indata, &iv2) { input the integer 13 }
read(indata, &sv1) { input the string /tmp/xxx }
read(indata, &fv1) { input the float 103.4 }
read(indata, &bv1) { input the boolean value on }
read(indata, &fv1) { input the float -8.3e-4 }
close(indata)
```

## Conversion Specifications

Conversion specifications define how the trailing arguments of `write` are converted and formatted. A conversion specification is a string that begins with `%` and ends with a conversion character describing how one argument is interpreted and formatted. The supported conversion characters are:

| Format char | Argument type | Output as                                                                                                                                                                                      |
| ----------- | ------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `B`         | Boolean       | "ON" or "OFF".                                                                                                                                                                                 |
| `B`         | Boolean       | "TRUE" or "FALSE".                                                                                                                                                                             |
| `U`         | Integer       | Unsigned integer.                                                                                                                                                                              |
| `D`, `I`    | Integer       | Decimal integer.                                                                                                                                                                               |
| `X`         | Integer       | Unsigned integer in hexadecimal (`abcdef` represent values 10 to 15).                                                                                                                          |
| `X`         | Integer       | Unsigned integer in hexadecimal (`ABCDEF` represent values 10 to 15).                                                                                                                          |
| `C`         | Integer       | The least significant byte is converted to a character and output.                                                                                                                             |
| `S`         | String        | String.                                                                                                                                                                                        |
| `F`         | Float         | The argument is converted to the form `[-]dd.dd`, where the number of digits after the decimal point equals the precision (default 6). If the precision is zero, no decimal point is printed.  |
| `e`, `E`    | Float         | As `F`, with an exponent in the form `[-]d.dddE(+/-)dd` and one digit before the decimal point. The case of the conversion character sets the case of the exponent letter.                     |
| `G`, `G`    | Float         | As `F` or `e` (or `E` for `G`), with the precision setting the number of significant digits. Trailing zeros are not printed, and a decimal point is printed only if it is followed by a digit. |

Between the `%` and the conversion character, the following modifiers may appear, in this order:

1. Flags, in any order: `-` left-adjusts the argument in its field (the default is right-justified); `+` always outputs a sign; a space prefixes a space if the first character is not a sign; `0` pads numeric conversions to the field width with leading zeros; `#` selects an alternate output form.
2. A minimum field width. The argument is output in a field at least this wide, padded (with spaces, or with zeros if the `0` flag is present) if it has fewer characters.
3. A period separating the field width from the precision.
4. The precision: the maximum number of characters output from a string, the number of digits after the decimal point for `e`, `E` or `F`, the number of significant digits for `G` or `G`, or the minimum number of digits for an integer.

**Examples:**

```
write("%d", iv1)      { print as a decimal integer }
write("%6d", iv1)     { print as a decimal integer, at least 6 characters wide }
write("%f", fv1)      { print as floating point }
write("%.2f", fv1)    { print as floating point, 2 digits after the decimal point }
write("%6.2f", fv1)   { at least 6 wide and 2 after the decimal point }
write("%+-6.2f", fv1) { at least 6 wide, 2 after the decimal point, left justified with a sign }
```

For a string variable containing "hello, world" (12 characters), the following shows the effect of various specifications. Colons mark the field edges:

```
:%s:       :hello, world:
:%10s:     :hello, world:
:%.10s:    :hello, wor:
:%-10s:    :hello, world:
:%.15s:    :hello, world:
:%-15s:    :hello, world :
:%15.10s:  : hello, wor:
:%-15.10s: :hello, wor :
```
