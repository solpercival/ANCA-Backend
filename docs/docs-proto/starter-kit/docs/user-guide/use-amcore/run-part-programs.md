# Run part programs

You can run part programs (NC programs) via a number of different interfaces.

When a part program is run, it will be activated in the relevant part program processor, and execution may also commence (depending on the interface and the arguments you supply).

The following subsections provide a brief overview of some (but not all) of the interfaces through which you can run part programs. You must use the correct procedure and syntax for the relevant interface.

## Using Active Program Display (APD)

You can use AMCore's Active Program Display (APD) application to run a part program:

1. Click **Program &rarr; Activate**.
2. Select your part program file, then click **Open**.
3. Use your main interface to run the part program, by clicking **Cycle Start**.

You can then use APD to deactivate the part program, by clicking **Program &rarr; Deactivate**.

## From another part program (CALLP)

From a part program, you can use an EPPL subprogram call (`CALLP`) to run a part program:

```
callp "<filepath>"
```

## From PLC code (sub-part-program devices)

From PLC code, you can use a PLCL sub-part-program device (e.g. `SPPGG`) to run a part program:

```
<subpp mnemonic> <subpp device number>
ppp (<ppp number>)
trigger (<condition>)
sppname ("<filepath>");
```

where `<subpp mnemonic>` is one of `sppgg` (Go-Go), `sppgs` (Go-Stop), `sppsg` (Stop-Go) or `sppss` (Stop-Stop).


## From the command prompt (PP_RUN)

From the command prompt, you can use the pp_run executable to run a part program:

```console
pp_run <filepath>
```

## From your application code (CNC Connect)

From your application code, you can call a CNC Connect function to run a part program. You may use one of the following functions:

```c
CnccProgramRun("<filepath>", <ppp number>, <program type>, <timeout>)
```
&emsp;&emsp;&emsp;&emsp;&emsp;OR
```c
CnccProgramRunAsync("<filepath>", <ppp number>, <program type>, <start>)
```

## Using a G-Code

From a part program, you can use a (canned cycle) G-Code to trigger its corresponding part program:

```
g# i0
```

where `#` is the G-Code number. This will run a *canned cycle* (a part program) named `g#.pp`, and is a convenient way to run an often-used part program.

Note the following:

* Some G-Codes are preparatory words that are reserved by AMCore and implement standard functionality.
* Other G-Codes trigger user-supplied canned cycles that may implement custom behaviour.
* A (canned cycle) G-Code (`g#`) must be programmed with at least one parameter (`i0`) or dimension word (`x0`) - or it will simply be ignored.


## Using an M-Code

From a part program, you can use a (mode 4) M-Code to trigger its corresponding part program:

```
{ A mode-4 M-Code }
m#
```

where `#` is the M-Code number. This will run a part program named `m#.pp`, and is a convenient way to run an often-used part program.

Note the following:

* Each M-Code may be configured (via relevant parameters) to use a specified mode (1-7). The mode specifies how the M-Code is implemented.
* Mode 4 (trailing subprogram call): These M-Codes are implemented via part programs. Upon processing such an M-Code, AMCore will trigger the corresponding part program.
* Modes 1-3 and 5-7 (PLC): These M-Code are implemented via PLC code. Upon processing such an M-Code, AMCore will instead trigger the PLC (by setting relevant bits).