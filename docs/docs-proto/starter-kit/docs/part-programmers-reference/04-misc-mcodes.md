# Miscellaneous Words (M-Codes)

Miscellaneous words can be programmed either as a M-code or a mnemonic name. The set of parameters shown below can be used to configure a M-code, where `<n>` is the M-code number

```
*mcode.<n>.name
*mcode.<n>.mode
```

There are seven modes which apply to miscellaneous words. For OEMs wishing to program M-Codes, refer to your AMCore Configuration Manual and AMCore PLC Programmer's Reference Manual for details.

## M-Code Modes

**Mode 1: Leading with Global Handshake**
A mode 1 M-Code will execute prior to most other commands within the standard block. All mode 1 and mode 2 M-Codes within a standard block will begin execution at the same time. The system will wait for **all** mode 1 *M-Codes to complete*[^1] before executing other commands in the standard block.

**Mode 2: Leading without Handshake**
A mode 2 M-Code will begin execution prior to most other commands within the standard block. All mode 1 and mode 2 M-Codes within a standard block will begin execution at the same time however, the system will continue execution of other commands in the standard block **without** waiting for any mode 2 M-Codes to complete. If however, mode 1 M-Codes are included in the standard block as well as mode 2 M-Codes, the rules associated with Mode 1 M-Codes takes precedence.

**Mode 3: Trailing with Global Handshake**
A mode 3 M-Code will begin execution after most other commands within the standard block have completed. The system will wait for **all** mode 3 M-Codes to complete before executing the remaining commands in the standard block and following blocks.

**Mode 4: (Sub) Part Program**
A mode 4 M-Code is a convenient way of calling an often used subprogram. The sub-program called will be `m<x>.pp` (where `<x>` is the number of the M-Code) in the directory determined by the parameter `dir.cc`. The system will wait for the M-Code to complete before continuing execution of following blocks.

**Mode 5: Leading with Private Handshake**
New Leading with HandShake (m_code[]/m_code[]). M-code Number Range: 0..1099.

**Mode 6: Leading Without Handshake**
New Leading without HandShake (m_code[]/none). M-code Number Range: 0..1099.

**Mode 7: Trailing with Private Handshake**
New Trailing with HandShake (m_code[]/m_code[]). M-code Number Range: 0..1099.

**Additional information:**

1. Program lookahead **is** broken by mode 4 M-Codes at the point of returning from the M-Code subprogram. Program lookahead is **not** broken by mode 1, mode 2 or mode 3 M-Codes.
2. Path compensation lookahead **is** broken by mode 4 M-Codes at the point of returning from the M-Code subprogram. Path compensation lookahead is **not** broken by mode 1, mode 2 or mode 3 M-Codes.
3. Velocity lookahead **is** broken by mode 1 and mode 3 M-Codes and by mode 4 M-Codes at the point of returning from the M-Code subprogram. Velocity lookahead is **not** broken by mode 2 M-Codes.

**Rules:**

1. More than one each of mode 1, 2 and 3 M-Codes may be programmed into a standard block, but each one *must be* unique (in other words, no M-Code or mnemonic should be repeated in a block).
2. Only one mode 4 M-Code is allowed in a standard block.
3. The maximum number of M-Codes which may be programmed into a standard block is 10.

---

## M-Code Reference

### `M0` — `stop`

Programmed stop.

| Property     | Value  |
| ------------ | ------ |
| **M-Code**   | `M0`   |
| **Mnemonic** | `stop` |
| **Mode**     | 7      |

**Syntax:**

```
M0 { or } stop
```

**Description:**

Programmed stop. This command will cause the machine to stop and drop out of cycle. CYCLE START must be pressed to resume execution. `stop` is often used in family of parts type programming, where parametric data is first entered and the machine drops out of cycle. After cycle start has been pressed, the machine may then begin motion.

**Additional information:**

1. `stop` does not stop program lookahead. If it is required to stop program lookahead as well (which is often the case), program a `sync` on the block following the stop command.
2. `stop` may be programmed anywhere within a program (including within a subroutine or compound block).

**Example:**

```
write("Enter the diameter to be cut")
read(&fv1)
write("\n\n PRESS CYCLE START\n TO BEGIN MACHINING...")
stop { Go out of cycle }
sync { Terminate program lookahead }
wclose { Close the "press cycle start" window after cycle start has been pressed }
{ Now begin machining process }
rapid X (fv1+0.2)
```

Prompts the operator for the diameter to cut and reads it into `fv1`, then drops out of cycle with `stop` so the value can be entered; after CYCLE START the `sync` terminates program lookahead, the prompt window is closed, and machining begins.

**See Also:** `optstop`, `sync`

---

### `M1` — `optstop`

Programmed optional stop.

| Property     | Value     |
| ------------ | --------- |
| **M-Code**   | `M1`      |
| **Mnemonic** | `optstop` |
| **Mode**     | 7         |

**Syntax:**

```
M1 { or } optstop
```

**Description:**

Programmed optional stop. Machine will stop if optional stop switch is *on*, until CYCLE START button is pressed. This feature is dependent on appropriate programming of the PLC.

**Additional information:**

1. `optstop` is identical in operation to `stop` except it looks at a switch input.
2. `optstop` may be programmed anywhere within a program (including within a subroutine or compound block).

**Example:**

```
optstop { Optional stop -- machine stops only if the optional stop switch is on }
```

Programs an optional stop. If the optional stop switch is on the machine drops out of cycle until CYCLE START is pressed; otherwise execution continues without stopping. The switch handling depends on the PLC.

**See Also:** `stop`, `sync`

---

### `M2` — `end`

End of program.

| Property     | Value |
| ------------ | ----- |
| **M-Code**   | `M2`  |
| **Mnemonic** | `end` |
| **Mode**     | 2     |

**Syntax:**

```
M2 { or } end
```

**Description:**

End of program. Program will rewind. This is optional, and is not required at the end of a main program as it is implied. If `end` is used in a sub program, then it will cause the sub program, all nested subprograms and the main program to be terminated and the main program to rewind. It is often used to escape from severe error conditions in deeply nested sub programs.

**Additional information:**

1. If a program has been executed as a sub program from the PLC, `end` will also automatically deactivate the program.
2. `end` may be programmed anywhere within a program (including within a subroutine or compound block).

**Example:**

```
end { End of program -- program rewinds }
```

Marks the end of the program; the program rewinds. When programmed inside a sub program it terminates that sub program, all nested sub programs, and the main program, then rewinds the main program.

**See Also:** `stop`, `optstop`

---

## Footnotes

[^1]: M-Code completion is determined by a rising edge on `XILB_M_FIN`.
