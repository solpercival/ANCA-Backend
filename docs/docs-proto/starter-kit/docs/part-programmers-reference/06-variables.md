# Variables

## Variables Classification

This section provides a summary of the scope, lifetime, lookahead considerations, index range and access syntax for the different classes and types of variables described in this chapter and also defines these terms.

### Variable Scope

The scope of a variable defines the boundaries for which the variable is implicitly accessible.

The scope of a variable will be one of:

- **Part Program:** Variable is defined locally to one part program or sub-part program. It may not be accessed from another part program.
- **PPP:** (Part Program Processor). A different variable of the same name exists for each part program processor. PPP1 is normally the main PPP used to run the machine.
- **PPP\*:** Same as PPP except that a PPP or PLC may reference the variable explicitly by using the modifier (PPPx) in front of the variable: where x=PPP number. eg:, `bv1` of the second PPP would be accessed as `(PPP2)bv1`.
- **CNC:** Variable is globally visible by all parts of the system. There is only one copy (ie: all references to this variable will access the same data).

### Variable Lifetime

The lifetime of a variable defines how long the data contained in a variable is maintained.

The lifetime of a variable will be one of:

- **Part Program Runtime (Volatile):** Contents of the variable are lost when the program: exits, rewinds or is deactivated.
- **AMCore Runtime (Volatile):** Contents of the variable are lost when AMCore is stopped or power to the CNC is switched OFF. When the CNC is powered up, these variables are all initialised according to their type as follows[^49]:

| Type    | Initial Value     |
| ------- | ----------------- |
| Boolean | `off`               |
| Integer | 0                 |
| Float   | 0.0               |
| String  | "" (Empty string) |

- **Non-Volatile:** Contents of the variable are NOT lost when AMCore is stopped or power to the CNC is switched OFF. They will generally only be initialised during commissioning and major servicing of a CNC (eg: complete system failure).

### Access Modifiers

An access modifier may precede a variable name.

An access modifier may be one of:

- **(PLC):** Access PLC variables.
- **(PPP):** Access the current PPP's variables.
- **(PPPx):** Access PPPx variables: where x=PPP number (1,2 ...).
- **(LM):** Access the current Logical machine's variables.
- **(LMx):**[^50] Access LMx variables: where x=logical machine number (1,2 ...).
- **(CNC):** Access CNC variables.

They are generally used to override default naming conventions for general purpose variables. Where this is particularly relevant is when part programs are accessing general purpose PLC variables. The PLC would access its general purpose PLC boolean variable number 2 as `bv2`. However, if the part programmer wished to read this variable, he could not use the name `bv2` as this would assume the part program general purpose boolean variable `bv2`. To access this variable, the programmer would have to use `(PLC)bv2`.

In the watch windows program and any library access to variables, preference is given to PPP variables if any ambiguity is encountered.

---

## Lookahead Considerations

For a detailed description of lookahead considerations, refer to the programmers guide.

The important things to remember with lookahead are:

1. Lookahead variables should NOT be used for communications between programs.
2. Using non-lookahead variables can be very confusing as they may be accessed well before the machine reaches the relevant block.

In the variables specification reference table, the variable lookahead status is shown in the LA column. A **Yes** indicates that the variable is a lookahead variable, an **No** indicates that the variable is not a lookahead variable.

---

## Variables

### `A`

Programmed dimension word `A` value or current command position of `A` axis in user frame coordinates.

| Property            | Value                                                                                                          |
| ------------------- | -------------------------------------------------------------------------------------------------------------- |
| **Type**            | float                                                                                                          |
| **Access Modifier** | PPP                                                                                                            |
| **Scope**           | PPP                                                                                                            |
| **Life Time**       | AMCore Runtime (Volatile)                                                                                      |
| **Lookahead**       | No                                                                                                             |
| **Units**           | Dimensionless or mm or inches or degrees, depending on current modal conditions and linear/rotary axis status. |

**Description:**

Programmed dimension word 'A' value or current command position of `A` axis in user frame coordinates. Dimension words are also accessible as variables, where the variable takes on its last programmed value; the `sync` command latches the last programmed machine position (in user frame coordinates) back into the dimension word variables.

**Example:**

```
sync
fv1 = A   { read the current A axis position }
```

After `sync` latches the machine position into the dimension word variables, the current `A` axis position (in user frame coordinates) is read into `fv1`.

**See Also:** `A`, `C`, `sync`

### `B`

Programmed dimension word `B` value or current command position of `B` axis in user frame coordinates.

| Property            | Value                                                                                                          |
| ------------------- | -------------------------------------------------------------------------------------------------------------- |
| **Type**            | float                                                                                                          |
| **Access Modifier** | PPP                                                                                                            |
| **Scope**           | PPP                                                                                                            |
| **Life Time**       | AMCore Runtime (Volatile)                                                                                      |
| **Lookahead**       | No                                                                                                             |
| **Units**           | Dimensionless or mm or inches or degrees, depending on current modal conditions and linear/rotary axis status. |

**Description:**

Programmed dimension word 'B' value or current command position of `B` axis in user frame coordinates. Dimension words are also accessible as variables, where the variable takes on its last programmed value; the `sync` command latches the last programmed machine position (in user frame coordinates) back into the dimension word variables.

**Example:**

```
sync
fv1 = B   { read the current B axis position }
```

After `sync` latches the machine position into the dimension word variables, the current `B` axis position (in user frame coordinates) is read into `fv1`.

**See Also:** `A`, `C`, `sync`

### `b_bv`

General purpose battery backed cnc boolean variables.

| Property            | Value                |
| ------------------- | -------------------- |
| **Type**            | boolean array [0-99] |
| **Access Modifier** | CNC                  |
| **Scope**           | CNC                  |
| **Life Time**       | Non-Volatile         |
| **Lookahead**       | No                   |

**Description:**

General purpose battery backed cnc boolean variables. Battery backed variables are identical in every respect to general purpose CNC variables except that they hold their value even while the CNC is switched off, and the (CNC) access modifier at the start of the name is optional (`(CNC)b_bv23` and `b_bv23` access the same variable).

**Example:**

```
b_bv5 = on   { set battery backed cnc boolean 5 }
if b_bv5 then
  write ( "flag retained across power cycle\n" )
ifend
```

Sets battery backed cnc boolean `b_bv5` on and later tests it. Because the variable is battery backed, its state is retained even if the CNC is powered off between the two operations.

**See Also:** `b_iv`, `b_fv`, `b_sv`, `gb_bv`, `bv`

### `b_fv`

General purpose battery backed cnc float variables.

| Property            | Value              |
| ------------------- | ------------------ |
| **Type**            | float array [0-99] |
| **Access Modifier** | CNC                |
| **Scope**           | CNC                |
| **Life Time**       | Non-Volatile       |
| **Lookahead**       | No                 |

**Description:**

General purpose battery backed cnc float variables. Battery backed variables are identical in every respect to general purpose CNC variables except that they hold their value even while the CNC is switched off, and the (CNC) access modifier at the start of the name is optional (`(CNC)b_fv23` and `b_fv23` access the same variable).

**Example:**

```
b_fv10 = 3.5   { store a battery backed cnc float }
fv1 = b_fv10 * 2.0
```

Stores the value 3.5 in battery backed cnc float `b_fv10` and reads it back into `fv1`. The stored value survives a power cycle because the variable is battery backed.

**See Also:** `b_bv`, `b_iv`, `b_sv`, `gb_fv`, `fv`

### `b_iv`

General purpose battery backed cnc integer variables.

| Property            | Value                |
| ------------------- | -------------------- |
| **Type**            | integer array [0-99] |
| **Access Modifier** | CNC                  |
| **Scope**           | CNC                  |
| **Life Time**       | Non-Volatile         |
| **Lookahead**       | No                   |

**Description:**

General purpose battery backed cnc integer variables. Battery backed variables are identical in every respect to general purpose CNC variables except that they hold their value even while the CNC is switched off, and the (CNC) access modifier at the start of the name is optional (`(CNC)b_iv23` and `b_iv23` access the same variable). 

**Example:**

```
{
  b_iv37 contains the number of finished parts.
  b_iv38 contains the number of partly completed parts.
}
sub cut_part
  b_iv38 = b_iv38 + 1   { Indicate that we have started a part }
  { Perform the cutting operation }
  b_iv37 = b_iv37 + 1   { Indicate that this was a completed part }
  b_iv38 = b_iv38 - 1
subend

if b_iv37 + (b_iv38/4.0) >= 25.0 then
  write ( "Please insert new cutting tool\n" )
  b_iv38 = 0
  b_iv37 = 0
ifend
```

Counts finished parts in `b_iv37` and partly completed parts in `b_iv38`. Because the counters are battery backed, the totals survive a power cycle, so the operator is prompted to fit a new cutting tool once 25 parts (counting each partly finished part as a quarter) have been produced, even across a machine shutdown.

**See Also:** `b_bv`, `b_fv`, `b_sv`, `gb_iv`, `iv`

### `b_sv`

General purpose battery backed cnc string variables.

| Property            | Value               |
| ------------------- | ------------------- |
| **Type**            | string array [0-49] |
| **Access Modifier** | CNC                 |
| **Scope**           | CNC                 |
| **Life Time**       | Non-Volatile        |
| **Lookahead**       | No                  |

**Description:**

General purpose battery backed cnc string variables. Battery backed variables are identical in every respect to general purpose CNC variables except that they hold their value even while the CNC is switched off, and the (CNC) access modifier at the start of the name is optional (`(CNC)b_sv23` and `b_sv23` access the same variable).

**Example:**

```
b_sv2 = "batch-A"
write ( b_sv2 )
```

Stores the string "batch-A" in battery backed cnc string `b_sv2` and writes it out. The stored text is retained even if the CNC is powered off.

**See Also:** `b_bv`, `b_iv`, `b_fv`, `gb_sv`, `sv`

### `biq`

PLC bistable device outputs.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | boolean array [0-499]     |
| **Access Modifier** | PLC                       |
| **Scope**           | PLC                       |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |

**Description:**

Outputs of the PLC bistable (set/reset latch) devices. A device's `biq` is latched on by its set input `bis`, latched off by its reset input `bir`, and inverted by its toggle input `bit`; the complementary output is `biz`. There are 500 bistable devices, indexed 0 to 499.

**Example:**

```
if biq4 then
  write ( "bistable 4 is set\n" )
ifend
```

Reads the output of PLC bistable device 4; `biq4` is on when the device is set.

**See Also:** `biz`, `bis`, `bir`, `bit`

### `bir`

PLC bistable device reset inputs.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | boolean array [0-499]     |
| **Access Modifier** | PLC                       |
| **Scope**           | PLC                       |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |

**Description:**

Reset inputs of the PLC bistable (set/reset latch) devices. Driving `bir` on for a device latches that device's output `biq` off (and its complementary output `biz` on). There are 500 bistable devices, indexed 0 to 499.

**Example:**

```
(plc)bir4 = on   { drive the reset input of bistable device 4 }
```

Drives the reset input of PLC bistable device 4, latching its output `biq4` off and its complementary output `biz4` on.

**See Also:** `bis`, `bit`, `biq`, `biz`

### `bis`

PLC bistable device set inputs.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | boolean array [0-499]     |
| **Access Modifier** | PLC                       |
| **Scope**           | PLC                       |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |

**Description:**

Set inputs of the PLC bistable (set/reset latch) devices. Driving `bis` on for a device latches that device's output `biq` on (and its complementary output `biz` off). There are 500 bistable devices, indexed 0 to 499.

**Example:**

```
(plc)bis4 = on   { drive the set input of bistable device 4 }
```

Drives the set input of PLC bistable device 4, latching its output `biq4` on and its complementary output `biz4` off.

**See Also:** `bir`, `bit`, `biq`, `biz`

### `bit`

PLC bistable device toggle inputs.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | boolean array [0-499]     |
| **Access Modifier** | PLC                       |
| **Scope**           | PLC                       |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |

**Description:**

Toggle inputs of the PLC bistable (set/reset latch) devices. Driving `bit` on for a device inverts that device's output `biq` (and its complementary output `biz`). There are 500 bistable devices, indexed 0 to 499.

**Example:**

```
(plc)bit4 = on   { drive the toggle input of bistable device 4 }
```

Drives the toggle input of PLC bistable device 4, inverting its output `biq4` and complementary output `biz4`.

**See Also:** `bis`, `bir`, `biq`, `biz`

### `biz`

PLC bistable device complementary (inverted) outputs.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | boolean array [0-499]     |
| **Access Modifier** | PLC                       |
| **Scope**           | PLC                       |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |

**Description:**

Complementary (inverted) outputs of the PLC bistable (set/reset latch) devices. A device's `biz` is the inverse of its output `biq`: it is on when the device is reset and off when the device is set. There are 500 bistable devices, indexed 0 to 499.

**Example:**

```
if biz4 then
  write ( "bistable 4 is reset\n" )
ifend
```

Reads the complementary output of PLC bistable device 4; `biz4` is on when the device is reset (the inverse of `biq4`).

**See Also:** `biq`, `bis`, `bir`, `bit`

### `bv`

Boolean variables.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | boolean array [0-99]      |
| **Access Modifier** | PPPx                      |
| **Scope**           | PPP*                      |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | Yes                       |

**Description:**

Boolean variables. Each Part Program Processor has its own array of 100 boolean variables, indexed 0 to 99. They may be accessed as `bv` or, with an explicit access modifier, as `(ppp)bv`.

**Example:**

```
bv2 = true   { set part-program boolean variable 2 }
```

Sets the current Part Program Processor's boolean variable 2 to `true`.

**See Also:** `iv`, `fv`, `sv`, `g_bv`

### `C`

Programmed dimension word 'C' value or current command position of `C` axis in user frame coordinates.

| Property            | Value                                                                                                          |
| ------------------- | -------------------------------------------------------------------------------------------------------------- |
| **Type**            | float                                                                                                          |
| **Access Modifier** | PPP                                                                                                            |
| **Scope**           | PPP                                                                                                            |
| **Life Time**       | AMCore Runtime (Volatile)                                                                                      |
| **Lookahead**       | No                                                                                                             |
| **Units**           | Dimensionless or mm or inches or degrees, depending on current modal conditions and linear/rotary axis status. |

**Description:**

Programmed dimension word 'C' value or current command position of `C` axis in user frame coordinates. Dimension words are also accessible as variables, where the variable takes on its last programmed value; the `sync` command latches the last programmed machine position (in user frame coordinates) back into the dimension word variables.

**Example:**

```
sync
fv1 = C   { read the current C axis position }
```

After `sync` latches the machine position into the dimension word variables, the current `C` axis position (in user frame coordinates) is read into `fv1`.

**See Also:** `A`, `C`, `sync`

### `cod`

PLC counter device direction inputs.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | boolean array [0-49]      |
| **Access Modifier** | PLC                       |
| **Scope**           | PLC                       |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |

**Description:**

Direction inputs of the PLC counter devices. The state of `cod` for a device selects the counting direction of that counter device. There are 50 counter devices, indexed 0 to 49.

**Example:**

```
(plc)cod4 = on   { set the count direction input of counter device 4 }
```

Drives the direction input of PLC counter device 4, selecting its counting direction.

**See Also:** `cor`, `coq`, `coz`, `cov`

### `coq`

PLC counter device outputs.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | boolean array [0-49]      |
| **Access Modifier** | PLC                       |
| **Scope**           | PLC                       |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |

**Description:**

Outputs of the PLC counter devices. `coq` for a device reflects that counter device's output state; its complement is `coz`. There are 50 counter devices, indexed 0 to 49.

**Example:**

```
bv0 = (plc)coq4   { read the output of counter device 4 }
```

Reads the output state of PLC counter device 4 into `bv0`.

**See Also:** `cod`, `cor`, `coz`, `cov`

### `cor`

PLC counter device reset inputs.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | boolean array [0-49]      |
| **Access Modifier** | PLC                       |
| **Scope**           | PLC                       |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |

**Description:**

Reset inputs of the PLC counter devices. Driving `cor` on for a device resets that counter device's accumulated count (`cov`). There are 50 counter devices, indexed 0 to 49.

**Example:**

```
(plc)cor4 = on   { reset counter device 4 }
```

Drives the reset input of PLC counter device 4, clearing its accumulated count `cov4`.

**See Also:** `cod`, `coq`, `coz`, `cov`

### `cov`

PLC counter device count values.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | integer array [0-49]      |
| **Access Modifier** | PLC                       |
| **Scope**           | PLC                       |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |

**Description:**

Current count values of the PLC counter devices. `cov` for a device holds that counter device's accumulated count. There are 50 counter devices, indexed 0 to 49.

**Example:**

```
iv0 = (plc)cov4   { read the current count of counter device 4 }
```

Reads the current accumulated count of PLC counter device 4 into `iv0`.

**See Also:** `cod`, `cor`, `coq`, `coz`

### `coz`

PLC counter device complementary outputs.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | boolean array [0-49]      |
| **Access Modifier** | PLC                       |
| **Scope**           | PLC                       |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |

**Description:**

Complementary outputs of the PLC counter devices. `coz` for a device is the inverse of that counter device's output `coq`. There are 50 counter devices, indexed 0 to 49.

**Example:**

```
bv0 = (plc)coz4   { read the complementary output of counter device 4 }
```

Reads the complementary output of PLC counter device 4 (the inverse of `coq4`) into `bv0`.

**See Also:** `cod`, `cor`, `coq`, `cov`

### `cs_iv`

Logical Machine cycle status integer variables.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | integer array [0-4]       |
| **Access Modifier** | LM                        |
| **Scope**           | LM                        |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |

**Description:**

Cycle status integer variables for the Logical Machine. Each Logical Machine has an array of 5 cycle status integer variables, indexed 0 to 4, accessed with the `(lm)` access modifier.

**Example:**

```
iv0 = (lm)cs_iv0   { read cycle status integer 0 of the current logical machine }
```

Reads cycle status integer variable 0 of the current Logical Machine into `iv0`.

**See Also:** `cs_sv`

### `cs_sv`

Logical Machine cycle status string variables.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | string array [0-4]        |
| **Access Modifier** | LM                        |
| **Scope**           | LM                        |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |

**Description:**

Cycle status string variables for the Logical Machine. Each Logical Machine has an array of 5 cycle status string variables, indexed 0 to 4, accessed with the `(lm)` access modifier.

**Example:**

```
sv0 = (lm)cs_sv0   { read cycle status string 0 of the current logical machine }
```

Reads cycle status string variable 0 of the current Logical Machine into `sv0`.

**See Also:** `cs_iv`

### `F`

Programmed feedrate word 'F' value.

| Property            | Value                                                                                                                                                                                     |
| ------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Type**            | float                                                                                                                                                                                     |
| **Access Modifier** | LM                                                                                                                                                                                        |
| **Scope**           | LM                                                                                                                                                                                        |
| **Life Time**       | AMCore Runtime (Volatile)                                                                                                                                                                 |
| **Lookahead**       | No                                                                                                                                                                                        |
| **Units**           | Programmed as: inches/min or inches/rev for inch mode; mm/min or mm/rev for metric mode. Read as: mm/min if programmed in feed/minute mode, mm/rev if programmed in feed/revolution mode. |

**Description:**

Programmed feedrate word 'F' value. Also accessible as `feedrate`.

**Example:**

```
F2440   
sync
fv0 = F
```

Sets the programmed feedrate to 2440 units in the current feedrate units; reads the current `F` value and stores it into `fv0`.

**See Also:** `feedrate`, `g_actual_feedrate`, `g_feedrate_units_group`

### `feedrate`

Programmed feedrate word 'F' value.

| Property            | Value                                                                                                                                                                                     |
| ------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Type**            | float                                                                                                                                                                                     |
| **Access Modifier** | LM                                                                                                                                                                                        |
| **Scope**           | LM                                                                                                                                                                                        |
| **Life Time**       | AMCore Runtime (Volatile)                                                                                                                                                                 |
| **Lookahead**       | No                                                                                                                                                                                        |
| **Units**           | Programmed as: inches/min or inches/rev for inch mode; mm/min or mm/rev for metric mode. Read as: mm/min if programmed in feed/minute mode, mm/rev if programmed in feed/revolution mode. |

**Description:**

Programmed feedrate word 'F' value. `feedrate` is the long name for the `F` word.

**Example:**

```
feedrate 2440   
sync
fv0 = feedrate
```

Sets the programmed feedrate to 2440 units in the current feedrate units; reads the current `feedrate` value and stores it into `fv0`.

**See Also:** `F`, `g_actual_feedrate`, `g_feedrate_units_group`

### `fv`

Float variables.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | float array [0-2199]      |
| **Access Modifier** | PPPx                      |
| **Scope**           | PPP*                      |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | Yes                       |

**Description:**

Floating-point variables. Each Part Program Processor has its own array of 2200 float variables, indexed 0 to 2199. They may be accessed as `fv` or, with an explicit access modifier, as `(ppp)fv`.

**Example:**

```
fv5 = 1.5   { set fv 5 }
```

Sets `fv5` to `1.5`.

**See Also:** `bv`, `iv`, `sv`, `g_fv`

### `g_accel`

Current path acceleration.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | float                     |
| **Access Modifier** | LM                        |
| **Scope**           | LM                        |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |
| **Units**           | mm/sec/sec                |

**Description:**

Current path acceleration. This variable may be written to; it takes effect only at block boundaries. It is a non-lookahead variable, so be careful of lookahead considerations if it is set from a part program.

**Example:**

```
g_accel = g_accel * 2
```

Doubles the current path acceleration.

**See Also:** `g_accel_oride`, `g_decel`, `g_radial_accel_limit`

### `g_accel_oride`

Current path acceleration override.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | float                     |
| **Access Modifier** | LM                        |
| **Scope**           | LM                        |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |
| **Units**           | dimensionless             |

**Description:**

Current path acceleration override. This override is a scale factor and is typically 1.0. This variable may be written to; it takes effect only at block boundaries. Be careful of lookahead considerations if it is set from a part program.

**Example:**

```
g_accel_oride = 0.8 * g_accel_oride
```

Scales the current acceleration override down to 80% of its previous value.

**See Also:** `g_accel`, `g_decel_oride`

### `g_actual_feedrate`

Current commanded feedrate within the VPI.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | float                     |
| **Access Modifier** | LM                        |
| **Scope**           | LM                        |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |
| **Units**           | mm/min                    |

**Description:**

Current feedrate commanded within the VPI after accounting for all the overrides.

**Example:**

```
current_feed = g_actual_feedrate
```

Reads the current commanded feedrate (after overrides) into `current_feed`.

**See Also:** `feedrate`, `g_est_actual_virtual_path_velocity`

### `g_bv`

General purpose boolean variables.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | boolean array [0-99]      |
| **Access Modifier** | PPPx                      |
| **Scope**           | PPP*                      |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | Yes                       |

**Description:**

General purpose boolean variables. Each Part Program Processor has its own array of 100 general purpose boolean variables, indexed 0 to 99. They may be accessed as `g_bv` or, with an explicit access modifier, as `(ppp)g_bv`.

**Example:**

```
g_bv5 = on   { set g_bv 5 }
```

Sets `g_bv5` to `on`.

**See Also:** `bv`, `g_iv`, `g_fv`, `g_sv`

### `g_crc_group`

Current mode (G code) for the CRC group of preparatory words.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | integer                   |
| **Access Modifier** | PPP                       |
| **Scope**           | PPP                       |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |

**Description:**

Current mode ("G code") for the CRC (cutter radius compensation) group of preparatory words.

**Example:**

```
if (g_crc_group = 42) then
  write("we are in CRCRIGHT mode")
ifend
```

Tests the CRC group modal state; a value of 42 means `crcright` mode is active.

**See Also:** `g_modal`, `g_interpolation_group`, `g_measurement_units_group`

### `g_crc_off`

CRC offset vector.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | float array [0-2]         |
| **Access Modifier** | LM                        |
| **Scope**           | LM                        |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |
| **Units**           | mm                        |

**Description:**

CRC offset vector from the programmed end point of the previous move to the offset end point of that move, indexed 0 to 2 for the I, J and K ordinates.

**Example:**

```
offs1 = g_crc_off[0]
```

Reads the I ordinate of the CRC offset vector into `offs1`.

**See Also:** `g_crc_group`

### `g_ct_jf`

Current programmed (target) position in joint frame coordinates within the coordinate transform module.

| Property            | Value                                            |
| ------------------- | ------------------------------------------------ |
| **Type**            | float array [0-19]                               |
| **Access Modifier** | CNC                                              |
| **Scope**           | CNC                                              |
| **Life Time**       | AMCore Runtime (Volatile)                        |
| **Lookahead**       | No                                               |
| **Units**           | mm for linear joints, degrees for rotary joints. |

**Description:**

Current programmed (target) position in **joint** frame coordinates within the coordinate transform module (CT). Unused ordinates are set to zero.

**Example:**

```
target_joint_4 = g_ct_jf3
```

Reads the CT target position of joint 4 (index 3) into `target_joint_4`.

**See Also:** `g_ct_pf`, `g_posn_jf`

### `g_ct_pf`

Current programmed (target) position in physical frame coordinates within the coordinate transform module.

| Property            | Value                                        |
| ------------------- | -------------------------------------------- |
| **Type**            | float array [0-19]                           |
| **Access Modifier** | CNC                                          |
| **Scope**           | CNC                                          |
| **Life Time**       | AMCore Runtime (Volatile)                    |
| **Lookahead**       | No                                           |
| **Units**           | mm for linear axes, degrees for rotary axes. |

**Description:**

Current programmed (target) position in **physical** frame coordinates within the coordinate transform module (CT). Unused ordinates are set to zero.

**Example:**

```
target_y = g_ct_pf[1]
```

Reads the CT target physical position of the `Y` axis (index 1) into `target_y`.

**See Also:** `g_ct_jf`, `g_posn_mf`

### `g_decel`

Current path deceleration.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | float                     |
| **Access Modifier** | LM                        |
| **Scope**           | LM                        |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |
| **Units**           | mm/sec/sec                |

**Description:**

Current path deceleration. This variable may be written to; it takes effect only at block boundaries. Be careful of lookahead considerations if it is set from a part program.

**Example:**

```
g_decel = g_decel * 2
```

Doubles the current path deceleration.

**See Also:** `g_decel_oride`, `g_accel`

### `g_decel_oride`

Current path deceleration override.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | float                     |
| **Access Modifier** | LM                        |
| **Scope**           | LM                        |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |
| **Units**           | dimensionless             |

**Description:**

Current path deceleration override. This override is a scale factor and is typically 1.0. This variable may be written to; it takes effect only at block boundaries. Be careful of lookahead considerations if it is set from a part program.

**Example:**

```
g_decel_oride = 0.8 * g_decel_oride
```

Scales the current deceleration override down to 80% of its previous value.

**See Also:** `g_decel`, `g_accel_oride`

### `g_dimension_mode_group`

Current mode (G code) for the Dimension Mode group of preparatory words.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | integer                   |
| **Access Modifier** | PPP                       |
| **Scope**           | PPP                       |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |

**Description:**

Current mode ("G code") for the Dimension Mode group of preparatory words.

**Example:**

```
if (g_dimension_mode_group = 90) then
  write("we are in ABSOLUTE mode")
ifend
```

Tests the dimension-mode group; a value of 90 means `absolute` mode is active.

**See Also:** `g_modal`, `g_measurement_units_group`

### `g_eff`

Current effector offsets.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | float array [0-2]         |
| **Access Modifier** | CNC                       |
| **Scope**           | CNC                       |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |
| **Units**           | mm                        |

**Description:**

Current effector offsets, indexed 0 to 2 for the I, J and K ordinates in that order.

**Example:**

```
eff_i = g_eff0
eff_j = g_eff1
eff_k = g_eff2
```

Reads the current I, J and K effector offsets into `eff_i`, `eff_j` and `eff_k`.

**See Also:** `g_eff_wheel`, `g_eff_adjust`, `g_to`

### `g_eff_adjust`

Current effector adjustment.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | float array [0-2]         |
| **Access Modifier** | LM                        |
| **Scope**           | LM                        |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |

**Description:**

The SMA variables `g_eff_adjust0`, `g_eff_adjust1` and `g_eff_adjust2` reflect the current value of the effector adjustment for the I, J and K ordinates respectively.

**Example:**

```
fv0 = g_eff_adjust0   { read the current effector adjustment for ordinate 0 }
```

Reads the current effector adjustment for ordinate 0 into `fv0`.

**See Also:** `g_eff`, `g_eff_wheel`

### `g_eff_wheel`

Wheel value set by the last eff statement.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | integer                   |
| **Access Modifier** | LM                        |
| **Scope**           | LM                        |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |

**Description:**

Holds the integer value following the `wheel` keyword of an `eff` statement, from where it may be retrieved into EPPL, viewed in a watch window, or logged. It is set to -1 by any `eff` statement that does not explicitly set it. The AMCore system does not use the value itself; it is transmitted to the optional 3DCimulator via the TPD stream.

**Example:**

```
iv0 = g_eff_wheel   { read the wheel value set by the last eff statement }
```

Reads the wheel value set by the most recent `eff` statement into `iv0`.

**See Also:** `g_eff`, `g_eff_adjust`

### `g_est_actual_virtual_path_velocity`

Current estimated actual virtual path velocity.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | float                     |
| **Access Modifier** | LM                        |
| **Scope**           | LM                        |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |
| **Units**           | mm/min                    |

**Description:**

Current estimated actual virtual path velocity commanded within the VPI after accounting for all the overrides.

**Example:**

```
current_actual_vpv = g_est_actual_virtual_path_velocity
```

Reads the current estimated actual virtual path velocity into `current_actual_vpv`.

**See Also:** `g_virtual_path_velocity`, `g_actual_feedrate`, `vpv`

### `g_ext_vel`

External velocity input increment.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | float                     |
| **Access Modifier** | LM                        |
| **Scope**           | LM                        |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |
| **Units**           | mm                        |

**Description:**

External velocity input increment. External velocity input is enabled by setting `ILB_ENABLE_EXTERNAL_VELOCITY` from the PLC and is filtered by the external_filter_gain and external_filter_bias parameters. It represents a positional increment to add to the current position of the machine on its programmed path (handled internally like an MPG velocity input) and is normally written to by the PLC or a dedicated C program.

**Example:**

```
fv0 = g_ext_vel   { read the external velocity input increment }
```

Reads the current external velocity input increment into `fv0`.

**See Also:** `g_actual_feedrate`

### `g_feedrate_units_group`

Current mode (G code) for the Feedrate Units group of preparatory words.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | integer                   |
| **Access Modifier** | PPP                       |
| **Scope**           | PPP                       |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |

**Description:**

Current mode ("G code") for the Feedrate Units group of preparatory words.

**Example:**

```
if (g_feedrate_units_group = 95) then
  write("we are in FEEDUPR mode")
ifend
```

Tests the feedrate-units group; a value of 95 means `feedupr` (feed per revolution) mode is active.

**See Also:** `g_modal`, `feedrate`

### `g_fo`

Current fixture offsets.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | float array [0-19]        |
| **Access Modifier** | CNC                       |
| **Scope**           | CNC                       |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |

**Description:**

Current fixture offsets.

**Example:**

```
fixture_z = g_fo[2]
```

Reads the current fixture offset of the `Z` axis (index 2) into `fixture_z`.

**See Also:** `g_lo`, `g_mo`, `g_wo`, `g_to`

### `g_fv`

General purpose float variables.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | float array [0-799]       |
| **Access Modifier** | PPPx                      |
| **Scope**           | PPP*                      |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | Yes                       |

**Description:**

General purpose floating-point variables. Each Part Program Processor has its own array of 800 general purpose float variables, indexed 0 to 799. They may be accessed as `g_fv` or, with an explicit access modifier, as `(ppp)g_fv`.

**Example:**

```
g_fv5 = 1.5   { set g_fv 5 }
```

Sets `g_fv5` to `1.5`.

**See Also:** `fv`, `g_bv`, `g_iv`, `g_sv`

### `g_interpolation_group`

Current mode (G code) for the Interpolation group of preparatory words.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | integer                   |
| **Access Modifier** | PPP                       |
| **Scope**           | PPP                       |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |

**Description:**

Current mode ("G code") for the Interpolation group of preparatory words.

**Example:**

```
if (g_interpolation_group = 0) then
  write("we are in RAPID mode")
ifend
```

Tests the interpolation group; a value of 0 means `rapid` mode is active.

**See Also:** `g_modal`, `g_spline_group`

### `g_iv`

General purpose integer variables.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | integer array [0-449]     |
| **Access Modifier** | PPPx                      |
| **Scope**           | PPP*                      |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | Yes                       |

**Description:**

General purpose integer variables. Each Part Program Processor has its own array of 450 general purpose integer variables, indexed 0 to 449. They may be accessed as `g_iv` or, with an explicit access modifier, as `(ppp)g_iv`.

**Example:**

```
g_iv5 = 42   { set g_iv 5 }
```

Sets `g_iv5` to `42`.

**See Also:** `iv`, `g_bv`, `g_fv`, `g_sv`

### `g_lm_stat`

Current Logical Machine status.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | integer                   |
| **Access Modifier** | LM                        |
| **Scope**           | LM                        |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |

**Description:**

Current status of the Logical Machine (LM). The value is 1 when the LM is dead, 2 when passive, 3 when idle and 4 when active; it is initialised to 1 (dead).

**Example:**

```
if (g_lm_stat = 4) then
  write("LM active")
ifend
```

Tests the Logical Machine status; a value of 4 means the LM is active.

**See Also:** `lm`

### `g_lo`

Current live offsets.

| Property            | Value                                        |
| ------------------- | -------------------------------------------- |
| **Type**            | float array [0-19]                           |
| **Access Modifier** | CNC                                          |
| **Scope**           | CNC                                          |
| **Life Time**       | AMCore Runtime (Volatile)                    |
| **Lookahead**       | No                                           |
| **Units**           | mm for linear axes, degrees for rotary axes. |

**Description:**

Current live offsets.

**Example:**

```
lo_z = g_lo[2]
```

Reads the current live offset of the `Z` axis (index 2) into `lo_z`.

**See Also:** `g_fo`, `g_mo`, `g_wo`

### `g_measurement_units_group`

Current mode (G code) for the Measurement Units group of preparatory words.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | integer                   |
| **Access Modifier** | PPP                       |
| **Scope**           | PPP                       |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |

**Description:**

Current mode ("G code") for the Measurement Units group of preparatory words.

**Example:**

```
if (g_measurement_units_group = 70) then
  write("we are in INCH mode")
ifend
```

Tests the measurement-units group; a value of 70 means `inch` mode is active.

**See Also:** `g_modal`, `g_dimension_mode_group`

### `g_mi`

Current mirror image.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | float array [0-19]        |
| **Access Modifier** | CNC                       |
| **Scope**           | CNC                       |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |

**Description:**

Current mirror image. Values are 1.0 for axes that do not have a mirror image active and -1.0 for axes that do have a mirror image active.

**Example:**

```
if g_mi11 < 0 then
  write("Mirror image on for C axis")
ifend
```

Tests the mirror-image flag of the `C` axis (index 11); a negative value means a mirror image is active for that axis.

**See Also:** `g_scale`, `g_nrs`

### `g_mo`

Current machine offsets.

| Property            | Value                                        |
| ------------------- | -------------------------------------------- |
| **Type**            | float array [0-19]                           |
| **Access Modifier** | CNC                                          |
| **Scope**           | CNC                                          |
| **Life Time**       | AMCore Runtime (Volatile)                    |
| **Lookahead**       | No                                           |
| **Units**           | mm for linear axes, degrees for rotary axes. |

**Description:**

Current machine offsets.

**Example:**

```
machine_offset_z = g_mo[2]
```

Reads the current machine offset of the `Z` axis (index 2) into `machine_offset_z`.

**See Also:** `g_fo`, `g_lo`, `g_wo`

### `g_modal`

Provides access to the programmed modal groups.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | integer array [0-11]      |
| **Access Modifier** | PPP                       |
| **Scope**           | PPP                       |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |

**Description:**

Provides access to the programmed modal groups. The value of each element represents the current "G code" programmed for that group. The array is indexed by group: `interpolation_group`, `spline_group`, `move_boundary_group`, `crc_group`, `measurement_units_group`, `dimension_mode_group`, `feedrate_units_group`, `spindle_units_group`, `spindless_units_group`, `spindlesss_units_group`, `spindlessss_units_group` and `retract_plane_group`.

**Example:**

```
if (g_modal[measurement_units_group] = 70) then
  write("we are in INCH mode")
ifend
```

Reads the measurement-units modal group via `g_modal`; a value of 70 means `inch` mode is active.

**See Also:** `g_crc_group`, `g_measurement_units_group`, `g_interpolation_group`

### `g_move_boundary_group`

Current mode (G code) for the Move Boundary group of preparatory words.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | integer                   |
| **Access Modifier** | PPP                       |
| **Scope**           | PPP                       |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |

**Description:**

Current mode ("G code") for the Move Boundary group of preparatory words.

**Example:**

```
if (g_move_boundary_group = 37) then
  write("we are in MBEXACT mode")
ifend
```

Tests the move-boundary group; a value of 37 means `mbexact` mode is active.

**See Also:** `g_modal`, `g_interpolation_group`

### `g_move_end_sf`

Target machine position at the end of the current move in selection frame coordinates.

| Property            | Value                                        |
| ------------------- | -------------------------------------------- |
| **Type**            | float array [0-19]                           |
| **Access Modifier** | LM                                           |
| **Scope**           | LM                                           |
| **Life Time**       | AMCore Runtime (Volatile)                    |
| **Lookahead**       | No                                           |
| **Units**           | mm for linear axes, degrees for rotary axes. |

**Description:**

Target machine position at the end of the current move in **selection** frame coordinates. Unused ordinates are set to zero. This variable is indexed by LM ordinate rather than by dimension word.

**Example:**

```
fv0 = g_move_end_sf0   { read target position of ordinate 1 at end of move }
```

Reads the target end-of-move position of LM ordinate 1 (index 0) into `fv0`.

**See Also:** `g_posn_mf`, `g_ct_pf`

### `g_nominal_radius`

Nominal radius of Axis Swap.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | float                     |
| **Access Modifier** | PPP                       |
| **Scope**           | PPP                       |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |
| **Units**           | mm                        |

**Description:**

Allows the user to set, view or restore the nominal radius of Axis Swap.

**Example:**

```
g_nominal_radius = 10.
axisswapon g_nominal_radius
```

Sets the nominal radius to 10 mm and uses it as the argument to `axisswapon`, so the previous nominal radius can be restored without specifying a fixed value again.

**See Also:** `axisswapon`

### `g_nrs`

Nominal radius scale.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | float array [0-19]        |
| **Access Modifier** | CNC                       |
| **Scope**           | CNC                       |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |

**Description:**

Nominal radius scale. For linear axes this value is 1.0. For rotary axes the value is nominal_radius * Pi/180.0, where nominal_radius is in mm.

**Example:**

```
dba_get_boolean_parm(&bv1, "a.rot_axis", "Dim.Rot_axis")
if bv1 = on then  { A is rotary }
  current_a_nomrad = g_nrs9 * 180.0 / Pi
ifend
```

If the `A` axis is rotary, recovers its nominal radius in mm from the scale factor `g_nrs9`.

**See Also:** `g_mi`, `g_scale`, `pi`

### `g_pnv`

Current plane normal vector.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | float array [0-2]         |
| **Access Modifier** | LM                        |
| **Scope**           | LM                        |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |
| **Units**           | mm                        |

**Description:**

Current plane normal vector, indexed 0 to 2 for the I, J and K ordinates.

**Example:**

```
plane_normal_i = g_pnv0
```

Reads the I ordinate of the current plane normal vector into `plane_normal_i`.

**See Also:** `g_crc_off`, `g_rot`

### `g_posn_jf`

Joint position in joint frame coordinates from a `posnlatch` block.

| Property            | Value                                            |
| ------------------- | ------------------------------------------------ |
| **Type**            | float array [0-19]                               |
| **Access Modifier** | PPP                                              |
| **Scope**           | PPP                                              |
| **Life Time**       | AMCore Runtime (Volatile)                        |
| **Lookahead**       | No                                               |
| **Units**           | mm for linear joints, degrees for rotary joints. |

**Description:**

Joint position in **joint** frame coordinates resulting from a `posnlatch` block. Unused ordinates are set to 0. Note that soft axes use a joint position.

**Example:**

```
joint_1_posn = g_posn_jf0
```

Reads the joint-frame position of joint 1 (latched by `posnlatch`) into `joint_1_posn`.

**See Also:** `g_posn_mf`, `g_posn_uf`, `g_probed_jf`

### `g_posn_mf`

Machine position in machine frame coordinates from a `posnlatch` block.

| Property            | Value                                        |
| ------------------- | -------------------------------------------- |
| **Type**            | float array [0-19]                           |
| **Access Modifier** | PPP                                          |
| **Scope**           | PPP                                          |
| **Life Time**       | AMCore Runtime (Volatile)                    |
| **Lookahead**       | No                                           |
| **Units**           | mm for linear axes, degrees for rotary axes. |

**Description:**

Machine position in **machine** frame coordinates resulting from a `posnlatch` block. Unused ordinates are set to zero.

**Example:**

```
machine_a_posn = g_posn_mf[9]
```

Reads the machine-frame position of the `A` axis (ordinate 10, index 9) latched by `posnlatch` into `machine_a_posn`.

**See Also:** `g_posn_jf`, `g_posn_uf`, `g_probed_mf`

### `g_posn_uf`

Machine position in user frame coordinates from a `posnlatch` block.

| Property            | Value                                        |
| ------------------- | -------------------------------------------- |
| **Type**            | float array [0-19]                           |
| **Access Modifier** | PPP                                          |
| **Scope**           | PPP                                          |
| **Life Time**       | AMCore Runtime (Volatile)                    |
| **Lookahead**       | No                                           |
| **Units**           | mm for linear axes, degrees for rotary axes. |

**Description:**

Machine position in **user** frame coordinates resulting from a `posnlatch` block. Unused ordinates are set to zero.

**Example:**

```
user_b_posn = g_posn_uf10
```

Reads the user-frame position of the `B` axis (index 10) latched by `posnlatch` into `user_b_posn`.

**See Also:** `g_posn_jf`, `g_posn_mf`, `g_probed_uf`

### `g_probed_jf`

Joint position in joint frame coordinates from a `probelatch` block.

| Property            | Value                                            |
| ------------------- | ------------------------------------------------ |
| **Type**            | float array [0-19]                               |
| **Access Modifier** | CNC                                              |
| **Scope**           | CNC                                              |
| **Life Time**       | AMCore Runtime (Volatile)                        |
| **Lookahead**       | No                                               |
| **Units**           | mm for linear joints, degrees for rotary joints. |

**Description:**

Joint position in **joint** frame coordinates resulting from a `probelatch` block. Unused ordinates are set to 0. Note that soft axes use a joint position.

**Example:**

```
joint_1_posn = g_probed_jf0
```

Reads the joint-frame position of joint 1 latched by `probelatch` into `joint_1_posn`.

**See Also:** `g_probed_mf`, `g_probed_uf`, `g_posn_jf`

### `g_probed_mf`

Machine position in machine frame coordinates from a `probelatch` block.

| Property            | Value                                        |
| ------------------- | -------------------------------------------- |
| **Type**            | float array [0-19]                           |
| **Access Modifier** | CNC                                          |
| **Scope**           | CNC                                          |
| **Life Time**       | AMCore Runtime (Volatile)                    |
| **Lookahead**       | No                                           |
| **Units**           | mm for linear axes, degrees for rotary axes. |

**Description:**

Machine position in **machine** frame coordinates resulting from a `probelatch` block. Unused ordinates are set to zero.

**Example:**

```
machine_a_posn = unitcv(g_probed_mf[9])
```

Reads the machine-frame position of the `A` axis (index 9) latched by `probelatch`, converting it to the current units with `unitcv`.

**See Also:** `g_probed_jf`, `g_probed_uf`, `g_posn_mf`

### `g_probed_uf`

Machine position in user frame coordinates from a `probelatch` block.

| Property            | Value                                        |
| ------------------- | -------------------------------------------- |
| **Type**            | float array [0-19]                           |
| **Access Modifier** | CNC                                          |
| **Scope**           | CNC                                          |
| **Life Time**       | AMCore Runtime (Volatile)                    |
| **Lookahead**       | No                                           |
| **Units**           | mm for linear axes, degrees for rotary axes. |

**Description:**

Machine position in **user** frame coordinates resulting from a `probelatch` block. Unused ordinates are set to zero.

**Example:**

```
user_b_posn = g_probed_uf10
```

Reads the user-frame position of the `B` axis (index 10) latched by `probelatch` into `user_b_posn`.

**See Also:** `g_probed_jf`, `g_probed_mf`, `g_posn_uf`

### `g_radial_accel_limit`

Current radial acceleration limit.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | float                     |
| **Access Modifier** | LM                        |
| **Scope**           | LM                        |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |
| **Units**           | mm/sec/sec                |

**Description:**

Current radial acceleration limit applied to the circular component of helical moves. This variable may be written to; it takes effect only at block boundaries. Be careful of lookahead considerations if it is set from a part program.

**Example:**

```
g_radial_accel_limit = 200
```

Sets the radial acceleration limit to 200 mm/sec/sec.

**See Also:** `g_accel`, `g_decel`

### `g_rot`

Current angle of rotation.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | float                     |
| **Access Modifier** | LM                        |
| **Scope**           | LM                        |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |
| **Units**           | degrees                   |

**Description:**

Current angle of rotation.

**Example:**

```
current_rot_angle = g_rot
```

Reads the current angle of rotation into `current_rot_angle`.

**See Also:** `g_pnv`

### `g_scale`

Current scale factor.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | float array [0-19]        |
| **Access Modifier** | CNC                       |
| **Scope**           | CNC                       |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |

**Description:**

Current scale factor.

**Example:**

```
scale_for_x = g_scale0
```

Reads the current scale factor of the `X` axis (index 0) into `scale_for_x`.

**See Also:** `g_mi`, `g_nrs`

### `g_servo_ap`

Actual joint position as read by the servo controller.

| Property            | Value                                            |
| ------------------- | ------------------------------------------------ |
| **Type**            | float array [0-19]                               |
| **Access Modifier** | CNC                                              |
| **Scope**           | CNC                                              |
| **Life Time**       | AMCore Runtime (Volatile)                        |
| **Lookahead**       | No                                               |
| **Units**           | mm for linear joints, degrees for rotary joints. |

**Description:**

Actual joint position in **joint** frame coordinates as currently read by the servo controller.

**Example:**

```
joint_1_feedback = g_servo_ap0
```

Reads the actual joint position of joint 1 from the servo controller into `joint_1_feedback`.

**See Also:** `g_servo_av`, `g_servo_cp`, `g_servo_cv`

### `g_servo_av`

Actual joint velocity as read by the servo controller.

| Property            | Value                                                    |
| ------------------- | -------------------------------------------------------- |
| **Type**            | float array [0-19]                                       |
| **Access Modifier** | CNC                                                      |
| **Scope**           | CNC                                                      |
| **Life Time**       | AMCore Runtime (Volatile)                                |
| **Lookahead**       | No                                                       |
| **Units**           | mm/min for linear joints, degrees/min for rotary joints. |

**Description:**

Actual joint velocity in **joint** frame coordinates as currently read by the servo controller.

**Example:**

```
joint_2_actual_velocity = g_servo_av1
```

Reads the actual velocity of joint 2 from the servo controller into `joint_2_actual_velocity`.

**See Also:** `g_servo_ap`, `g_servo_cv`, `g_servo_cp`

### `g_servo_cp`

Command joint position used by the servo controller.

| Property            | Value                                            |
| ------------------- | ------------------------------------------------ |
| **Type**            | float array [0-19]                               |
| **Access Modifier** | CNC                                              |
| **Scope**           | CNC                                              |
| **Life Time**       | AMCore Runtime (Volatile)                        |
| **Lookahead**       | No                                               |
| **Units**           | mm for linear joints, degrees for rotary joints. |

**Description:**

Command joint position in **joint** frame coordinates as currently being used by the servo controller.

**Example:**

```
joint_1_command = g_servo_cp0
```

Reads the command position of joint 1 used by the servo controller into `joint_1_command`.

**See Also:** `g_servo_cv`, `g_servo_ap`, `g_servo_av`

### `g_servo_cv`

Command joint velocity derived from the command position.

| Property            | Value                                                    |
| ------------------- | -------------------------------------------------------- |
| **Type**            | float array [0-19]                                       |
| **Access Modifier** | CNC                                                      |
| **Scope**           | CNC                                                      |
| **Life Time**       | AMCore Runtime (Volatile)                                |
| **Lookahead**       | No                                                       |
| **Units**           | mm/min for linear joints, degrees/min for rotary joints. |

**Description:**

Command joint velocity, derived from the command position.

**Example:**

```
joint_2_cmd_velocity = g_servo_cv1
```

Reads the command velocity of joint 2 into `joint_2_cmd_velocity`.

**See Also:** `g_servo_cp`, `g_servo_ap`, `g_servo_av`

### `g_spindle_units_group`

Current mode (G code) for the Spindle Speed Units group of preparatory words.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | integer                   |
| **Access Modifier** | PPP                       |
| **Scope**           | PPP                       |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |

**Description:**

Current mode ("G code") for the Spindle Speed Units group of preparatory words.

**Example:**

```
if (g_spindle_units_group = 96) then
  write("we are in CSSON mode")
ifend
```

Tests the spindle-speed-units group for spindle 1; a value of 96 means `csson` (constant surface speed) mode is active.

**See Also:** `g_spindless_units_group`, `g_modal`, `spindle`

### `g_spindless_units_group`

Current mode (G code) for the Spindle Speed Units (2nd spindle) group of preparatory words.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | integer                   |
| **Access Modifier** | PPP                       |
| **Scope**           | PPP                       |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |

**Description:**

Current mode ("G code") for the Spindle Speed Units group of preparatory words for the second spindle.

**Example:**

```
if (g_spindless_units_group = 196) then
  write("we are in CSSONSS mode")
ifend
```

Tests the spindle-speed-units group for spindle 2; a value of 196 means `cssonss` mode is active.

**See Also:** `g_spindle_units_group`, `g_spindlesss_units_group`, `spindless`

### `g_spindlesss_units_group`

Current mode (G code) for the Spindle Speed Units (3rd spindle) group of preparatory words.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | integer                   |
| **Access Modifier** | PPP                       |
| **Scope**           | PPP                       |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |

**Description:**

Current mode ("G code") for the Spindle Speed Units group of preparatory words for the third spindle.

**Example:**

```
if (g_spindlesss_units_group = 296) then
  write("we are in CSSONSSS mode")
ifend
```

Tests the spindle-speed-units group for spindle 3; a value of 296 means `cssonsss` mode is active.

**See Also:** `g_spindless_units_group`, `g_spindlessss_units_group`, `spindlesss`

### `g_spindlessss_units_group`

Current mode (G code) for the Spindle Speed Units (4th spindle) group of preparatory words.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | integer                   |
| **Access Modifier** | PPP                       |
| **Scope**           | PPP                       |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |

**Description:**

Current mode ("G code") for the Spindle Speed Units group of preparatory words for the fourth spindle.

**Example:**

```
if (g_spindlessss_units_group = 396) then
  write("we are in CSSONSSSS mode")
ifend
```

Tests the spindle-speed-units group for spindle 4; a value of 396 means `cssonssss` mode is active.

**See Also:** `g_spindlesss_units_group`, `g_modal`, `spindlessss`

### `g_spline_group`

Current mode (G code) for the Spline group of preparatory words.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | integer                   |
| **Access Modifier** | PPP                       |
| **Scope**           | PPP                       |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |

**Description:**

Current mode ("G code") for the Spline group of preparatory words.

**Example:**

```
if (g_spline_group = 60) then
  write("we are in SPLINEON mode")
ifend
```

Tests the spline group; a value of 60 means `splineon` mode is active.

**See Also:** `g_modal`, `g_interpolation_group`, `st`, `tf`

### `g_sv`

General purpose string variables.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | string array [0-49]       |
| **Access Modifier** | PPPx                      |
| **Scope**           | PPP*                      |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | Yes                       |

**Description:**

General purpose string variables. Each Part Program Processor has its own array of 50 general purpose string variables, indexed 0 to 49. They may be accessed as `g_sv` or, with an explicit access modifier, as `(ppp)g_sv`.

**Example:**

```
g_sv5 = "text"   { set g_sv 5 }
```

Sets `g_sv5` to `"text"`.

**See Also:** `sv`, `g_bv`, `g_iv`, `g_fv`

### `g_to`

Current tool offsets.

| Property            | Value                                        |
| ------------------- | -------------------------------------------- |
| **Type**            | float array [0-19]                           |
| **Access Modifier** | CNC                                          |
| **Scope**           | CNC                                          |
| **Life Time**       | AMCore Runtime (Volatile)                    |
| **Lookahead**       | No                                           |
| **Units**           | mm for linear axes, degrees for rotary axes. |

**Description:**

Current tool offsets.

**Example:**

```
tool_offset_z = g_to[2]
```

Reads the current tool offset of the `Z` axis (index 2) into `tool_offset_z`.

**See Also:** `g_tool_t`, `g_fo`, `g_wo`

### `g_tool_t`

Tool table entries.

| Property            | Value                                        |
| ------------------- | -------------------------------------------- |
| **Type**            | float array [0-24]                           |
| **Access Modifier** | CNC                                          |
| **Scope**           | CNC                                          |
| **Life Time**       | AMCore Runtime (Volatile)                    |
| **Lookahead**       | No                                           |
| **Units**           | mm for linear axes, degrees for rotary axes. |

**Description:**

Tool table entries. Each tool occupies 24 consecutive elements: axes X, Y, Z, U, V, W, P, Q, R, A, B, C, X', Y', Z', U', V', A', B', C' followed by I, J, K and `rad` in that order.

**Example:**

```
tool_offset_z = g_tool_t[(tool_number) * 24 + 2]
```

Reads the Z tool offset of tool `tool_number` from the tool table by indexing 24 elements per tool.

**See Also:** `g_to`, `g_eff`

### `g_tpg_fv`

Simulation-graphics floating-point communications array.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | float array [0-15]        |
| **Access Modifier** | CNC                       |
| **Scope**           | CNC                       |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |

**Description:**

Simulation-graphics floating-point communications array used by the tool-path display generator, indexed 0 to 15.

**Example:**

```
val = g_tpg_fv0
```

Reads element 0 of the simulation-graphics floating-point communications array into `val`.

**See Also:** `g_tpg_modal`

### `g_tpg_modal`

Simulation-graphics modal bits.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | boolean array [0-3]       |
| **Access Modifier** | CNC                       |
| **Scope**           | CNC                       |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |

**Description:**

Simulation-graphics modal bits used by the tool-path display generator, indexed 0 to 3. Bit 0 is set while the machine is running in simulation (dry-run) mode.

**Example:**

```
if g_tpg_modal0 then
  write("simulation mode")
ifend
```

Tests bit 0 of the simulation-graphics modal word, which is set while the machine is running in simulation (dry-run) mode.

**See Also:** `g_tpg_fv`

### `g_virtual_path_length`

`vpl` value of the current move.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | float                     |
| **Access Modifier** | LM                        |
| **Scope**           | LM                        |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |
| **Units**           | mm                        |

**Description:**

`vpl` (virtual path length) value of the current move being executed.

**Example:**

```
fv0 = g_virtual_path_length   { read vpl of the current move }
```

Reads the virtual path length of the current move into `fv0`.

**See Also:** `g_virtual_path_velocity`, `vpl`, `vpv`

### `g_virtual_path_velocity`

`vpv` value of the current move.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | float                     |
| **Access Modifier** | LM                        |
| **Scope**           | LM                        |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |
| **Units**           | mm/min                    |

**Description:**

`vpv` (virtual path velocity) value of the current move being executed.

**Example:**

```
fv0 = g_virtual_path_velocity   { read vpv of the current move }
```

Reads the virtual path velocity of the current move into `fv0`.

**See Also:** `g_virtual_path_length`, `g_est_actual_virtual_path_velocity`, `vpv`

### `g_wo`

Current workpiece offsets.

| Property            | Value                                        |
| ------------------- | -------------------------------------------- |
| **Type**            | float array [0-19]                           |
| **Access Modifier** | CNC                                          |
| **Scope**           | CNC                                          |
| **Life Time**       | AMCore Runtime (Volatile)                    |
| **Lookahead**       | No                                           |
| **Units**           | mm for linear axes, degrees for rotary axes. |

**Description:**

Current workpiece offsets. Because workpiece offsets are programmed via a position preset, the values in this array will generally not equal the values programmed during a workpiece (G50) block.

**Example:**

```
work_offset_z = g_wo[2]
```

Reads the current workpiece offset of the `Z` axis (index 2) into `work_offset_z`.

**See Also:** `g_fo`, `g_lo`, `g_mo`, `g_to`

### `gb_bv`

General purpose battery backed cnc boolean variables.

| Property            | Value                 |
| ------------------- | --------------------- |
| **Type**            | boolean array [0-499] |
| **Access Modifier** | CNC                   |
| **Scope**           | CNC                   |
| **Life Time**       | Non-Volatile          |
| **Lookahead**       | No                    |

**Description:**

General purpose battery backed cnc boolean variables. They are identical to general purpose CNC booleans except that they retain their value while the CNC is switched off, and the `(CNC)` access modifier is optional. There are 500 variables, indexed 0 to 499.

**Example:**

```
gb_bv5 = on   { set gb_bv 5 }
```

Sets `gb_bv5` to `on`.

**See Also:** `gb_iv`, `gb_fv`, `gb_sv`, `b_bv`

### `gb_fv`

General purpose battery backed cnc float variables.

| Property            | Value               |
| ------------------- | ------------------- |
| **Type**            | float array [0-999] |
| **Access Modifier** | CNC                 |
| **Scope**           | CNC                 |
| **Life Time**       | Non-Volatile        |
| **Lookahead**       | No                  |

**Description:**

General purpose battery backed cnc float variables. They are identical to general purpose CNC floats except that they retain their value while the CNC is switched off, and the `(CNC)` access modifier is optional. There are 1000 variables, indexed 0 to 999.

**Example:**

```
gb_fv5 = 1.5   { set gb_fv 5 }
```

Sets `gb_fv5` to `1.5`.

**See Also:** `gb_bv`, `gb_iv`, `gb_sv`, `b_fv`

### `gb_iv`

General purpose battery backed cnc integer variables.

| Property            | Value                 |
| ------------------- | --------------------- |
| **Type**            | integer array [0-479] |
| **Access Modifier** | CNC                   |
| **Scope**           | CNC                   |
| **Life Time**       | Non-Volatile          |
| **Lookahead**       | No                    |

**Description:**

General purpose battery backed cnc integer variables. They are identical to general purpose CNC integers except that they retain their value while the CNC is switched off, and the `(CNC)` access modifier is optional. There are 480 variables, indexed 0 to 479.

**Example:**

```
gb_iv5 = 42   { set gb_iv 5 }
```

Sets `gb_iv5` to `42`.

**See Also:** `gb_bv`, `gb_fv`, `gb_sv`, `b_iv`

### `gb_sv`

General purpose battery backed cnc string variables.

| Property            | Value               |
| ------------------- | ------------------- |
| **Type**            | string array [0-49] |
| **Access Modifier** | CNC                 |
| **Scope**           | CNC                 |
| **Life Time**       | Non-Volatile        |
| **Lookahead**       | No                  |

**Description:**

General purpose battery backed cnc string variables. They are identical to general purpose CNC strings except that they retain their value while the CNC is switched off, and the `(CNC)` access modifier is optional. There are 50 variables, indexed 0 to 49.

**Example:**

```
gb_sv5 = "text"   { set gb_sv 5 }
```

Sets `gb_sv5` to `"text"`.

**See Also:** `gb_bv`, `gb_iv`, `gb_fv`, `b_sv`

### `H`

Programmed extra word 'H' value.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | integer                   |
| **Access Modifier** | PPP                       |
| **Scope**           | PPP                       |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |

**Description:**

Programmed extra word 'H' value. Tool offset group when CRC is programmed using an indirect radius definition.

**Example:**

```
iv0 = H   { read the programmed H word }
```

Reads the programmed extra word 'H' value into `iv0`.

**See Also:** `rad`, `I`, `J`, `K`

### `I`

Programmed interpolation word 'I' value.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | float                     |
| **Access Modifier** | PPP                       |
| **Scope**           | PPP                       |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |
| **Units**           | dimensionless             |

**Description:**

Programmed interpolation word 'I' value.

**Example:**

```
fv0 = I   { read the programmed I interpolation word }
```

Reads the programmed interpolation word 'I' value into `fv0`.

**See Also:** `J`, `K`, `rad`

### `il`

Bit (boolean) access to the input logical variables.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | boolean array [0-511]     |
| **Access Modifier** | PPP                       |
| **Scope**           | PPP*                      |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |

**Description:**

Bit (boolean) access to the input logical variables; `il` is an alias for `ilb`. `il5` and `ilb5` access the same input logical boolean.

**Example:**

```
bv0 = il5   { read il 5 }
```

Reads the value of `il5` into `bv0`.

**See Also:** `ilb`, `ili`, `ol`

### `ilb`

Input logical boolean variables.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | boolean array [0-511]     |
| **Access Modifier** | PPP                       |
| **Scope**           | PPP*                      |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |

**Description:**

Input logical boolean variables. They reflect the state of the logical inputs available to a part program processor. There are 512 input logical booleans, indexed 0 to 511. They may also be accessed by the bit alias `il`.

**Example:**

```
bv0 = ilb5   { read ilb 5 }
```

Reads the value of `ilb5` into `bv0`.

**See Also:** `il`, `ili`, `ilf`, `ils`, `olb`

### `ilf`

Input logical float variables.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | float array [0-9]         |
| **Access Modifier** | PPP                       |
| **Scope**           | PPP*                      |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |

**Description:**

Input logical float variables. There are 10 input logical floats, indexed 0 to 9.

**Example:**

```
fv0 = ilf5   { read ilf 5 }
```

Reads the value of `ilf5` into `fv0`.

**See Also:** `ilb`, `ili`, `ils`

### `ili`

Input logical integer variables.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | integer array [0-47]      |
| **Access Modifier** | PPP                       |
| **Scope**           | PPP*                      |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |

**Description:**

Input logical integer variables. There are 48 input logical integers, indexed 0 to 47.

**Example:**

```
iv0 = ili5   { read ili 5 }
```

Reads the value of `ili5` into `iv0`.

**See Also:** `ilb`, `ilf`, `ils`

### `ils`

Input logical string variables.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | string array [0-4]        |
| **Access Modifier** | PPP                       |
| **Scope**           | PPP*                      |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |

**Description:**

Input logical string variables. There are 5 input logical strings, indexed 0 to 4.

**Example:**

```
sv0 = ils5   { read ils 5 }
```

Reads the value of `ils5` into `sv0`.

**See Also:** `ilb`, `ili`, `ilf`

### `ip`

Bit (boolean) access to the input physical variables.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | boolean array [0-3299]    |
| **Access Modifier** | PLC                       |
| **Scope**           | CNC                       |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |

**Description:**

Bit (boolean) access to the input physical variables; `ip` is an alias for `ipb`. `ip5` and `ipb5` access the same input physical boolean.

**Example:**

```
bv0 = ip5   { read ip 5 }
```

Reads the value of `ip5` into `bv0`.

**See Also:** `ipb`, `ipi`, `op`

### `ipb`

Input physical boolean variables.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | boolean array [0-3299]    |
| **Access Modifier** | PLC                       |
| **Scope**           | CNC                       |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |

**Description:**

Input physical boolean variables. These are the physical (hardware) logical inputs, CNC scope, indexed 0 to 3299. They may also be accessed by the bit alias `ip`.

**Example:**

```
bv0 = ipb5   { read ipb 5 }
```

Reads the value of `ipb5` into `bv0`.

**See Also:** `ip`, `ipi`, `ipf`, `ips`, `opb`

### `ipf`

Input physical float variables.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | float array [0-159]       |
| **Access Modifier** | PLC                       |
| **Scope**           | CNC                       |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |

**Description:**

Input physical float variables, indexed 0 to 159.

**Example:**

```
fv0 = ipf5   { read ipf 5 }
```

Reads the value of `ipf5` into `fv0`.

**See Also:** `ipb`, `ipi`, `ips`

### `ipi`

Input physical integer variables.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | integer array [0-791]     |
| **Access Modifier** | PLC                       |
| **Scope**           | CNC                       |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |

**Description:**

Input physical integer variables, indexed 0 to 791.

**Example:**

```
iv0 = ipi5   { read ipi 5 }
```

Reads the value of `ipi5` into `iv0`.

**See Also:** `ipb`, `ipf`, `ips`

### `ips`

Input physical string variables.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | string array [0-4]        |
| **Access Modifier** | PLC                       |
| **Scope**           | CNC                       |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |

**Description:**

Input physical string variables, indexed 0 to 4.

**Example:**

```
sv0 = ips5   { read ips 5 }
```

Reads the value of `ips5` into `sv0`.

**See Also:** `ipb`, `ipi`, `ipf`

### `iv`

Integer variables.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | integer array [0-99]      |
| **Access Modifier** | PPPx                      |
| **Scope**           | PPP*                      |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | Yes                       |

**Description:**

Integer variables. Each Part Program Processor has its own array of 100 integer variables, indexed 0 to 99. They may be accessed as `iv` or, with an explicit access modifier, as `(ppp)iv`.

**Example:**

```
iv0 = 42   { set part-program integer variable 0 }
```

Sets the current Part Program Processor's integer variable 0 to `42`.

**See Also:** `bv`, `fv`, `sv`, `g_iv`

### `J`

Programmed interpolation word 'J' value.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | float                     |
| **Access Modifier** | PPP                       |
| **Scope**           | PPP                       |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |
| **Units**           | dimensionless             |

**Description:**

Programmed interpolation word 'J' value.

**Example:**

```
fv0 = J   { read the programmed J interpolation word }
```

Reads the programmed interpolation word 'J' value into `fv0`.

**See Also:** `I`, `K`, `rad`

### `K`

Programmed interpolation word 'K' value.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | float                     |
| **Access Modifier** | PPP                       |
| **Scope**           | PPP                       |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |
| **Units**           | dimensionless             |

**Description:**

Programmed interpolation word 'K' value.

**Example:**

```
fv0 = K   { read the programmed K interpolation word }
```

Reads the programmed interpolation word 'K' value into `fv0`.

**See Also:** `I`, `J`, `rad`

### `ol`

Bit (boolean) access to the output logical variables.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | boolean array [0-511]     |
| **Access Modifier** | PPP                       |
| **Scope**           | PPP*                      |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |

**Description:**

Bit (boolean) access to the output logical variables; `ol` is an alias for `olb`. `ol5` and `olb5` access the same output logical boolean.

**Example:**

```
ol5 = on   { drive ol 5 }
```

Sets `ol5` to `on`.

**See Also:** `olb`, `oli`, `il`

### `olb`

Output logical boolean variables.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | boolean array [0-511]     |
| **Access Modifier** | PPP                       |
| **Scope**           | PPP*                      |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |

**Description:**

Output logical boolean variables. They drive the logical outputs from a part program processor. There are 512 output logical booleans, indexed 0 to 511. They may also be accessed by the bit alias `ol`.

**Example:**

```
olb5 = on   { drive olb 5 }
```

Sets `olb5` to `on`.

**See Also:** `ol`, `oli`, `olf`, `ols`, `ilb`

### `olf`

Output logical float variables.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | float array [0-9]         |
| **Access Modifier** | PPP                       |
| **Scope**           | PPP*                      |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |

**Description:**

Output logical float variables. There are 10 output logical floats, indexed 0 to 9.

**Example:**

```
olf5 = 1.5   { set olf 5 }
```

Sets `olf5` to `1.5`.

**See Also:** `olb`, `oli`, `ols`

### `oli`

Output logical integer variables.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | integer array [0-47]      |
| **Access Modifier** | PPP                       |
| **Scope**           | PPP*                      |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |

**Description:**

Output logical integer variables. There are 48 output logical integers, indexed 0 to 47.

**Example:**

```
oli5 = 42   { set oli 5 }
```

Sets `oli5` to `42`.

**See Also:** `olb`, `olf`, `ols`

### `ols`

Output logical string variables.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | string array [0-4]        |
| **Access Modifier** | PPP                       |
| **Scope**           | PPP*                      |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |

**Description:**

Output logical string variables. There are 5 output logical strings, indexed 0 to 4.

**Example:**

```
ols5 = "text"   { set ols 5 }
```

Sets `ols5` to `"text"`.

**See Also:** `olb`, `oli`, `olf`

### `op`

Bit (boolean) access to the output physical variables.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | boolean array [0-3299]    |
| **Access Modifier** | PLC                       |
| **Scope**           | CNC                       |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |

**Description:**

Bit (boolean) access to the output physical variables; `op` is an alias for `opb`. `op5` and `opb5` access the same output physical boolean.

**Example:**

```
op5 = on   { set op 5 }
```

Sets `op5` to `on`.

**See Also:** `opb`, `opi`, `ip`

### `opb`

Output physical boolean variables.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | boolean array [0-3299]    |
| **Access Modifier** | PLC                       |
| **Scope**           | CNC                       |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |

**Description:**

Output physical boolean variables. These are the physical (hardware) logical outputs, CNC scope, indexed 0 to 3299. They may also be accessed by the bit alias `op`.

**Example:**

```
opb5 = on   { set opb 5 }
```

Sets `opb5` to `on`.

**See Also:** `op`, `opi`, `opf`, `ops`, `ipb`

### `opf`

Output physical float variables.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | float array [0-159]       |
| **Access Modifier** | PLC                       |
| **Scope**           | CNC                       |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |

**Description:**

Output physical float variables, indexed 0 to 159.

**Example:**

```
opf5 = 1.5   { set opf 5 }
```

Sets `opf5` to `1.5`.

**See Also:** `opb`, `opi`, `ops`

### `opi`

Output physical integer variables.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | integer array [0-791]     |
| **Access Modifier** | PLC                       |
| **Scope**           | CNC                       |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |

**Description:**

Output physical integer variables, indexed 0 to 791.

**Example:**

```
opi5 = 42   { set opi 5 }
```

Sets `opi5` to `42`.

**See Also:** `opb`, `opf`, `ops`

### `ops`

Output physical string variables.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | string array [0-4]        |
| **Access Modifier** | PLC                       |
| **Scope**           | CNC                       |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |

**Description:**

Output physical string variables, indexed 0 to 4.

**Example:**

```
ops5 = "text"   { set ops 5 }
```

Sets `ops5` to `"text"`.

**See Also:** `opb`, `opi`, `opf`

### `osc_active`

Number of currently active oscillators.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | integer                   |
| **Access Modifier** | CNC                       |
| **Scope**           | CNC                       |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |

**Description:**

Number of oscillators currently active. It is incremented as each axis is started oscillating and gives the extent of the active portion of the `osc_index` map.

**Example:**

```
count = osc_active
```

Reads the number of currently active oscillators into `count`.

**See Also:** `osc_index`, `osc_enable`, `osc_global_enable`

### `osc_amplitude`

Programmed peak-to-peak oscillation amplitude per axis.

| Property            | Value                                        |
| ------------------- | -------------------------------------------- |
| **Type**            | float array [0-47]                           |
| **Access Modifier** | CNC                                          |
| **Scope**           | CNC                                          |
| **Life Time**       | AMCore Runtime (Volatile)                    |
| **Lookahead**       | No                                           |
| **Units**           | mm for linear axes, degrees for rotary axes. |

**Description:**

Programmed peak-to-peak amplitude of the oscillation for each axis dimension (the amplitude argument of the `oscillate` function), indexed 0 to 47.

**Example:**

```
amp = osc_amplitude5
```

Reads the programmed peak-to-peak oscillation amplitude of axis dimension 5 into `amp`.

**See Also:** `osc_velocity`, `osc_offset`, `osc_dwell_pos`, `osc_dwell_neg`, `oscillate`

### `osc_dwell_neg`

Programmed dwell time at the negative end of the oscillation per axis.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | float array [0-47]        |
| **Access Modifier** | CNC                       |
| **Scope**           | CNC                       |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |
| **Units**           | seconds                   |

**Description:**

Programmed dwell time at the negative end of the oscillation for each axis dimension (the dwell_neg argument of the `oscillate` function), indexed 0 to 47.

**Example:**

```
dwell = osc_dwell_neg5
```

Reads the programmed dwell time at the negative end of the oscillation for axis dimension 5 into `dwell`.

**See Also:** `osc_dwell_pos`, `osc_amplitude`, `oscillate`

### `osc_dwell_pos`

Programmed dwell time at the positive end of the oscillation per axis.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | float array [0-47]        |
| **Access Modifier** | CNC                       |
| **Scope**           | CNC                       |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |
| **Units**           | seconds                   |

**Description:**

Programmed dwell time at the positive end of the oscillation for each axis dimension (the dwell_pos argument of the `oscillate` function), indexed 0 to 47.

**Example:**

```
dwell = osc_dwell_pos5
```

Reads the programmed dwell time at the positive end of the oscillation for axis dimension 5 into `dwell`.

**See Also:** `osc_dwell_neg`, `osc_amplitude`, `oscillate`

### `osc_enable`

Per-axis oscillator enable flags.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | boolean array [0-47]      |
| **Access Modifier** | CNC                       |
| **Scope**           | CNC                       |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |

**Description:**

Per-axis oscillator enable flags, indexed by axis dimension 0 to 47. A flag is set when its axis is started oscillating and cleared to request that the oscillation stop.

**Example:**

```
if osc_enable5 then
  write("axis 5 oscillating")
ifend
```

Tests whether the oscillator on axis dimension 5 is enabled.

**See Also:** `osc_active`, `osc_index`, `osc_global_enable`

### `osc_global_enable`

Master enable for the oscillator subsystem.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | boolean                   |
| **Access Modifier** | CNC                       |
| **Scope**           | CNC                       |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |

**Description:**

Master enable flag for the trapezoidal and sinusoidal oscillator subsystem. When off, no axis oscillates regardless of the individual `osc_enable` flags.

**Example:**

```
if osc_global_enable then
  write("oscillators enabled")
ifend
```

Tests the master oscillator enable flag; it is on while the oscillator subsystem is enabled.

**See Also:** `osc_active`, `osc_enable`, `oscillate`

### `osc_index`

Map of active oscillator slots to axis dimension indices.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | integer array [0-47]      |
| **Access Modifier** | CNC                       |
| **Scope**           | CNC                       |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |

**Description:**

Maps each active oscillator slot (0 to `osc_active` minus 1) to the axis dimension index it drives; unused slots hold -1. Indexed 0 to 47.

**Example:**

```
axis_dim = osc_index0
```

Reads the axis dimension index driven by the first active oscillator slot (index 0) into `axis_dim`; unused slots hold -1.

**See Also:** `osc_active`, `osc_enable`

### `osc_offset`

Programmed oscillation offset shift per axis.

| Property            | Value                                        |
| ------------------- | -------------------------------------------- |
| **Type**            | float array [0-47]                           |
| **Access Modifier** | CNC                                          |
| **Scope**           | CNC                                          |
| **Life Time**       | AMCore Runtime (Volatile)                    |
| **Lookahead**       | No                                           |
| **Units**           | mm for linear axes, degrees for rotary axes. |

**Description:**

Programmed offset shift that moves the centre of the oscillation for each axis dimension (the offset_shift argument of the `oscillate` function), indexed 0 to 47.

**Example:**

```
offs = osc_offset5
```

Reads the programmed oscillation offset shift of axis dimension 5 into `offs`.

**See Also:** `osc_amplitude`, `osc_velocity`, `oscillate`

### `osc_velocity`

Programmed maximum oscillation velocity per axis.

| Property            | Value                                                |
| ------------------- | ---------------------------------------------------- |
| **Type**            | float array [0-47]                                   |
| **Access Modifier** | CNC                                                  |
| **Scope**           | CNC                                                  |
| **Life Time**       | AMCore Runtime (Volatile)                            |
| **Lookahead**       | No                                                   |
| **Units**           | mm/min for linear axes, degrees/min for rotary axes. |

**Description:**

Programmed maximum velocity the oscillator attains for each axis dimension (the feedrate argument of the `oscillate` function), indexed 0 to 47.

**Example:**

```
vel = osc_velocity5
```

Reads the programmed maximum oscillation velocity of axis dimension 5 into `vel`.

**See Also:** `osc_amplitude`, `osc_offset`, `oscillate`

### `P`

Programmed dimension word 'P' value or current command position of `P` axis in user frame coordinates.

| Property            | Value                                                                                                          |
| ------------------- | -------------------------------------------------------------------------------------------------------------- |
| **Type**            | float                                                                                                          |
| **Access Modifier** | PPP                                                                                                            |
| **Scope**           | PPP                                                                                                            |
| **Life Time**       | AMCore Runtime (Volatile)                                                                                      |
| **Lookahead**       | No                                                                                                             |
| **Units**           | Dimensionless or mm or inches or degrees, depending on current modal conditions and linear/rotary axis status. |

**Description:**

Programmed dimension word 'P' value or current command position of `P` axis in user frame coordinates. Dimension words are also accessible as variables, where the variable takes on its last programmed value; the `sync` command latches the last programmed machine position (in user frame coordinates) back into the dimension word variables.

**Example:**

```
sync
fv1 = P   { read the current P axis position }
```

After `sync` latches the machine position into the dimension word variables, the current `P` axis position (in user frame coordinates) is read into `fv1`.

**See Also:** `A`, `C`, `sync`

### `Q`

Programmed dimension word 'Q' value or current command position of `Q` axis in user frame coordinates.

| Property            | Value                                                                                                          |
| ------------------- | -------------------------------------------------------------------------------------------------------------- |
| **Type**            | float                                                                                                          |
| **Access Modifier** | PPP                                                                                                            |
| **Scope**           | PPP                                                                                                            |
| **Life Time**       | AMCore Runtime (Volatile)                                                                                      |
| **Lookahead**       | No                                                                                                             |
| **Units**           | Dimensionless or mm or inches or degrees, depending on current modal conditions and linear/rotary axis status. |

**Description:**

Programmed dimension word 'Q' value or current command position of `Q` axis in user frame coordinates. Dimension words are also accessible as variables, where the variable takes on its last programmed value; the `sync` command latches the last programmed machine position (in user frame coordinates) back into the dimension word variables.

**Example:**

```
sync
fv1 = Q   { read the current Q axis position }
```

After `sync` latches the machine position into the dimension word variables, the current `Q` axis position (in user frame coordinates) is read into `fv1`.

**See Also:** `A`, `C`, `sync`

### `R`

Programmed dimension word 'R' value or current command position of `R` axis in user frame coordinates.

| Property            | Value                                                                                                          |
| ------------------- | -------------------------------------------------------------------------------------------------------------- |
| **Type**            | float                                                                                                          |
| **Access Modifier** | PPP                                                                                                            |
| **Scope**           | PPP                                                                                                            |
| **Life Time**       | AMCore Runtime (Volatile)                                                                                      |
| **Lookahead**       | No                                                                                                             |
| **Units**           | Dimensionless or mm or inches or degrees, depending on current modal conditions and linear/rotary axis status. |

**Description:**

Programmed dimension word 'R' value or current command position of `R` axis in user frame coordinates. Dimension words are also accessible as variables, where the variable takes on its last programmed value; the `sync` command latches the last programmed machine position (in user frame coordinates) back into the dimension word variables.

**Example:**

```
sync
fv1 = R   { read the current R axis position }
```

After `sync` latches the machine position into the dimension word variables, the current `R` axis position (in user frame coordinates) is read into `fv1`.

**See Also:** `A`, `C`, `sync`

### `rad`

Programmed extra word '`rad`' value.

| Property            | Value                                                                 |
| ------------------- | --------------------------------------------------------------------- |
| **Type**            | float                                                                 |
| **Access Modifier** | PPP                                                                   |
| **Scope**           | PPP                                                                   |
| **Life Time**       | AMCore Runtime (Volatile)                                             |
| **Lookahead**       | No                                                                    |
| **Units**           | Programmed as: inches for inch mode, mm for metric mode. Read as: mm. |

**Description:**

Programmed extra word '`rad`' value. CRC radius when programmed using an explicit radius specification.

**Example:**

```
fv0 = rad   { read the programmed rad word }
```

Reads the programmed extra word '`rad`' value into `fv0`.

**See Also:** `I`, `J`, `K`, `H`

### `S`

Programmed spindle 1 speed word 'S' value.

| Property            | Value                                                                                                                                                                               |
| ------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Type**            | float                                                                                                                                                                               |
| **Access Modifier** | PPP                                                                                                                                                                                 |
| **Scope**           | PPP                                                                                                                                                                                 |
| **Life Time**       | AMCore Runtime (Volatile)                                                                                                                                                           |
| **Lookahead**       | No                                                                                                                                                                                  |
| **Units**           | Programmed as: ft/min for inch mode with CSS mode, m/min for metric mode with CSS mode, RPM for RPM mode. Read as: mm/min if programmed in CSS mode, RPM if programmed in RPM mode. |

**Description:**

Programmed spindle speed (for spindle 1) word 'S' value. Also accessible as `spindle`.

**Example:**

```
fv0 = S   { read the programmed spindle 1 speed word }
```

Reads the programmed spindle 1 speed word 'S' value into `fv0`.

**See Also:** `spindle`, `spindless`, `g_spindle_units_group`

### `spindle`

Programmed spindle 1 speed word 'S' value.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | float                     |
| **Access Modifier** | PPP                       |
| **Scope**           | PPP                       |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |
| **Units**           | As for `S`.               |

**Description:**

Programmed spindle speed (for spindle 1) word. `spindle` is the long name for the `S` word.

**Example:**

```
fv0 = spindle   { read the programmed spindle 1 speed }
```

Reads the programmed spindle 1 speed into `fv0`.

**See Also:** `S`, `spindless`, `g_spindle_units_group`

### `spindless`

Programmed spindle 2 speed word '`ss`' value.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | float                     |
| **Access Modifier** | PPP                       |
| **Scope**           | PPP                       |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |
| **Units**           | As for `S`.               |

**Description:**

Programmed spindle speed (for spindle 2) word '`ss`' value. `spindless` is the long name for the `ss` word.

**Example:**

```
fv0 = spindless   { read the programmed spindle 2 speed }
```

Reads the programmed spindle 2 speed into `fv0`.

**See Also:** `ss`, `spindle`, `spindlesss`, `g_spindless_units_group`

### `spindlesss`

Programmed spindle 3 speed word '`sss`' value.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | float                     |
| **Access Modifier** | PPP                       |
| **Scope**           | PPP                       |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |
| **Units**           | As for `S`.               |

**Description:**

Programmed spindle speed (for spindle 3) word '`sss`' value. `spindlesss` is the long name for the `sss` word.

**Example:**

```
fv0 = spindlesss   { read the programmed spindle 3 speed }
```

Reads the programmed spindle 3 speed into `fv0`.

**See Also:** `sss`, `spindless`, `spindlessss`, `g_spindlesss_units_group`

### `spindlessss`

Programmed spindle 4 speed word '`ssss`' value.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | float                     |
| **Access Modifier** | PPP                       |
| **Scope**           | PPP                       |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |
| **Units**           | As for `S`.               |

**Description:**

Programmed spindle speed (for spindle 4) word '`ssss`' value. `spindlessss` is the long name for the `ssss` word.

**Example:**

```
fv0 = spindlessss   { read the programmed spindle 4 speed }
```

Reads the programmed spindle 4 speed into `fv0`.

**See Also:** `ssss`, `spindlesss`, `g_spindlessss_units_group`

### `ss`

Programmed spindle 2 speed word '`ss`' value.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | float                     |
| **Access Modifier** | PPP                       |
| **Scope**           | PPP                       |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |
| **Units**           | As for `S`.               |

**Description:**

Programmed spindle speed (for spindle 2) word '`ss`' value. Also accessible as `spindless`.

**Example:**

```
fv0 = ss   { read the programmed spindle 2 speed word }
```

Reads the programmed spindle 2 speed word '`ss`' value into `fv0`.

**See Also:** `spindless`, `S`, `sss`, `g_spindless_units_group`

### `sss`

Programmed spindle 3 speed word '`sss`' value.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | float                     |
| **Access Modifier** | PPP                       |
| **Scope**           | PPP                       |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |
| **Units**           | As for `S`.               |

**Description:**

Programmed spindle speed (for spindle 3) word '`sss`' value. Also accessible as `spindlesss`.

**Example:**

```
fv0 = sss   { read the programmed spindle 3 speed word }
```

Reads the programmed spindle 3 speed word '`sss`' value into `fv0`.

**See Also:** `spindlesss`, `ss`, `ssss`, `g_spindlesss_units_group`

### `ssss`

Programmed spindle 4 speed word '`ssss`' value.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | float                     |
| **Access Modifier** | PPP                       |
| **Scope**           | PPP                       |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |
| **Units**           | As for `S`.               |

**Description:**

Programmed spindle speed (for spindle 4) word '`ssss`' value. Also accessible as `spindlessss`.

**Example:**

```
fv0 = ssss   { read the programmed spindle 4 speed word }
```

Reads the programmed spindle 4 speed word '`ssss`' value into `fv0`.

**See Also:** `spindlessss`, `sss`, `g_spindlessss_units_group`

### `st`

Programmed extra word '`st`' value.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | integer                   |
| **Access Modifier** | PPP                       |
| **Scope**           | PPP                       |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |
| **Units**           | dimensionless             |

**Description:**

Programmed extra word '`st`' value. Spline type when used in spline mode interpolation. May take the values `chord` or `uniform`.

**Example:**

```
iv0 = st   { read the programmed spline type word }
```

Reads the programmed spline type word '`st`' value into `iv0`.

**See Also:** `tf`, `g_spline_group`

### `sv`

String variables.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | string array [0-47]       |
| **Access Modifier** | PPPx                      |
| **Scope**           | PPP*                      |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | Yes                       |

**Description:**

String variables. Each Part Program Processor has its own array of 48 string variables, indexed 0 to 47. They may be accessed as `sv` or, with an explicit access modifier, as `(ppp)sv`.

**Example:**

```
sv5 = "text"   { set sv 5 }
```

Sets `sv5` to `"text"`.

**See Also:** `bv`, `iv`, `fv`, `g_sv`

### `tf`

Programmed extra word '`tf`' value.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | float                     |
| **Access Modifier** | PPP                       |
| **Scope**           | PPP                       |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |
| **Units**           | dimensionless             |

**Description:**

Programmed extra word '`tf`' value. Tension factor when used in spline mode interpolation. Has a value between 0 and 1.0.

**Example:**

```
fv0 = tf   { read the programmed tension factor word }
```

Reads the programmed extra word '`tf`' value into `fv0`.

**See Also:** `st`, `g_spline_group`

### `tie`

PLC timer enable inputs.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | boolean array [0-1999]    |
| **Access Modifier** | PLC                       |
| **Scope**           | PLC                       |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |

**Description:**

Enable inputs of the PLC timer devices. While a timer's `tie` is on the timer accumulates elapsed time; clearing it holds the timer. There are 2000 timer devices, indexed 0 to 1999.

**Example:**

```
(plc)tie4 = on   { enable timer 4 }
```

Enables PLC timer 4 so that it accumulates elapsed time.

**See Also:** `tir`, `tiq`, `tiz`, `tip`, `tiv`

### `tip`

PLC timer preset times.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | integer array [0-1999]    |
| **Access Modifier** | PLC                       |
| **Scope**           | PLC                       |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |
| **Units**           | milliseconds              |

**Description:**

Preset (target) times of the PLC timer devices, in milliseconds. When a timer's elapsed time `tiv` reaches its `tip`, its output `tiq` turns on. There are 2000 timer devices, indexed 0 to 1999.

**Example:**

```
(plc)tip4 = 1000   { preset timer 4 to 1000 ms }
```

Sets the preset of PLC timer 4 to 1000 milliseconds, after which its output `tiq4` turns on.

**See Also:** `tie`, `tir`, `tiq`, `tiz`, `tiv`

### `tiq`

PLC timer outputs.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | boolean array [0-1999]    |
| **Access Modifier** | PLC                       |
| **Scope**           | PLC                       |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |

**Description:**

Outputs of the PLC timer devices. A timer's `tiq` turns on when its elapsed time `tiv` reaches its preset tip. There are 2000 timer devices, indexed 0 to 1999.

**Example:**

```
if tiq4 then
  write("timer 4 expired")
ifend
```

Tests the output of PLC timer 4, which turns on once its elapsed time reaches its preset.

**See Also:** `tie`, `tir`, `tiz`, `tip`, `tiv`

### `tir`

PLC timer reset inputs.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | boolean array [0-1999]    |
| **Access Modifier** | PLC                       |
| **Scope**           | PLC                       |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |

**Description:**

Reset inputs of the PLC timer devices. Driving a timer's `tir` on clears its output `tiq` and resets its elapsed time `tiv` to zero. There are 2000 timer devices, indexed 0 to 1999.

**Example:**

```
(plc)tir4 = on   { reset timer 4 }
```

Resets PLC timer 4, clearing its output `tiq4` and its elapsed time `tiv4`.

**See Also:** `tie`, `tiq`, `tiz`, `tip`, `tiv`

### `tiv`

PLC timer elapsed times.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | integer array [0-1999]    |
| **Access Modifier** | PLC                       |
| **Scope**           | PLC                       |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |
| **Units**           | milliseconds              |

**Description:**

Elapsed times of the PLC timer devices, in milliseconds, accumulated while the timer is enabled (`tie` on) and reset to zero by `tir`. There are 2000 timer devices, indexed 0 to 1999.

**Example:**

```
elapsed = tiv4
```

Reads the elapsed time of PLC timer 4, in milliseconds, into `elapsed`.

**See Also:** `tie`, `tir`, `tiq`, `tiz`, `tip`

### `tiz`

PLC timer complementary (inverted) outputs.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | boolean array [0-1999]    |
| **Access Modifier** | PLC                       |
| **Scope**           | PLC                       |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |

**Description:**

Complementary (inverted) outputs of the PLC timer devices. A timer's `tiz` is the inverse of its output `tiq`. There are 2000 timer devices, indexed 0 to 1999.

**Example:**

```
if tiz4 then
  write("timer 4 still running")
ifend
```

Tests the complementary output of PLC timer 4, which is on until the timer reaches its preset (the inverse of `tiq4`).

**See Also:** `tie`, `tir`, `tiq`, `tip`, `tiv`

### `U`

Programmed dimension word 'U' value or current command position of `U` axis in user frame coordinates.

| Property            | Value                                                                                                          |
| ------------------- | -------------------------------------------------------------------------------------------------------------- |
| **Type**            | float                                                                                                          |
| **Access Modifier** | PPP                                                                                                            |
| **Scope**           | PPP                                                                                                            |
| **Life Time**       | AMCore Runtime (Volatile)                                                                                      |
| **Lookahead**       | No                                                                                                             |
| **Units**           | Dimensionless or mm or inches or degrees, depending on current modal conditions and linear/rotary axis status. |

**Description:**

Programmed dimension word 'U' value or current command position of `U` axis in user frame coordinates. Dimension words are also accessible as variables, where the variable takes on its last programmed value; the `sync` command latches the last programmed machine position (in user frame coordinates) back into the dimension word variables.

**Example:**

```
sync
fv1 = U   { read the current U axis position }
```

After `sync` latches the machine position into the dimension word variables, the current `U` axis position (in user frame coordinates) is read into `fv1`.

**See Also:** `A`, `C`, `sync`

### `V`

Programmed dimension word 'V' value or current command position of `V` axis in user frame coordinates.

| Property            | Value                                                                                                          |
| ------------------- | -------------------------------------------------------------------------------------------------------------- |
| **Type**            | float                                                                                                          |
| **Access Modifier** | PPP                                                                                                            |
| **Scope**           | PPP                                                                                                            |
| **Life Time**       | AMCore Runtime (Volatile)                                                                                      |
| **Lookahead**       | No                                                                                                             |
| **Units**           | Dimensionless or mm or inches or degrees, depending on current modal conditions and linear/rotary axis status. |

**Description:**

Programmed dimension word 'V' value or current command position of `V` axis in user frame coordinates. Dimension words are also accessible as variables, where the variable takes on its last programmed value; the `sync` command latches the last programmed machine position (in user frame coordinates) back into the dimension word variables.

**Example:**

```
sync
fv1 = V   { read the current V axis position }
```

After `sync` latches the machine position into the dimension word variables, the current `V` axis position (in user frame coordinates) is read into `fv1`.

**See Also:** `A`, `C`, `sync`

### `vpl`

Virtual path length feedrate word.

| Property            | Value                                   |
| ------------------- | --------------------------------------- |
| **Type**            | float                                   |
| **Access Modifier** | LM                                      |
| **Scope**           | LM                                      |
| **Life Time**       | AMCore Runtime (Volatile)               |
| **Lookahead**       | No                                      |
| **Units**           | mm in metric mode, inches in inch mode. |

**Description:**

Virtual path length word, used in G150/`feedvpvl` mode together with `vpv`. It specifies the move length along the path; AMCore uses `vpl`/`vpv` to derive the machine feedrate for the move. `vpl` cannot be zero, and every move (except rapids) must have both a `vpv` and a `vpl` command.

**Example:**

```
G1 X0.3 VPV20 VPL0.2   { move to X0.3 at virtual path velocity 20, path length 0.2 }
```

Commands a linear move to X0.3 with a virtual path length of 0.2 and a virtual path velocity of 20, from which AMCore derives the machine feedrate.

**See Also:** `vpv`, `g_virtual_path_length`, `feedrate`

### `vpv`

Virtual path velocity feedrate word.

| Property            | Value                                           |
| ------------------- | ----------------------------------------------- |
| **Type**            | float                                           |
| **Access Modifier** | LM                                              |
| **Scope**           | LM                                              |
| **Life Time**       | AMCore Runtime (Volatile)                       |
| **Lookahead**       | No                                              |
| **Units**           | mm/min in metric mode, inches/min in inch mode. |

**Description:**

Virtual path velocity word, used in G150/`feedvpvl` mode together with `vpl`. It specifies the desired velocity along the path; AMCore uses `vpl`/`vpv` to derive the machine feedrate for the move. Every move (except rapids) must have both a `vpv` and a `vpl` command.

**Example:**

```
G1 X0.3 VPV20 VPL0.2   { move to X0.3 at virtual path velocity 20, path length 0.2 }
```

Commands a linear move to X0.3 with a virtual path velocity of 20 and a virtual path length of 0.2, from which AMCore derives the machine feedrate.

**See Also:** `vpl`, `g_virtual_path_velocity`, `feedrate`

### `W`

Programmed dimension word 'W' value or current command position of `W` axis in user frame coordinates.

| Property            | Value                                                                                                          |
| ------------------- | -------------------------------------------------------------------------------------------------------------- |
| **Type**            | float                                                                                                          |
| **Access Modifier** | PPP                                                                                                            |
| **Scope**           | PPP                                                                                                            |
| **Life Time**       | AMCore Runtime (Volatile)                                                                                      |
| **Lookahead**       | No                                                                                                             |
| **Units**           | Dimensionless or mm or inches or degrees, depending on current modal conditions and linear/rotary axis status. |

**Description:**

Programmed dimension word 'W' value or current command position of `W` axis in user frame coordinates. Dimension words are also accessible as variables, where the variable takes on its last programmed value; the `sync` command latches the last programmed machine position (in user frame coordinates) back into the dimension word variables.

**Example:**

```
sync
fv1 = W   { read the current W axis position }
```

After `sync` latches the machine position into the dimension word variables, the current `W` axis position (in user frame coordinates) is read into `fv1`.

**See Also:** `A`, `C`, `sync`

### `X`

Programmed dimension word 'X' value or current command position of `X` axis in user frame coordinates.

| Property            | Value                                                                                                          |
| ------------------- | -------------------------------------------------------------------------------------------------------------- |
| **Type**            | float                                                                                                          |
| **Access Modifier** | PPP                                                                                                            |
| **Scope**           | PPP                                                                                                            |
| **Life Time**       | AMCore Runtime (Volatile)                                                                                      |
| **Lookahead**       | No                                                                                                             |
| **Units**           | Dimensionless or mm or inches or degrees, depending on current modal conditions and linear/rotary axis status. |

**Description:**

Programmed dimension word 'X' value or current command position of `X` axis in user frame coordinates. Dimension words are also accessible as variables, where the variable takes on its last programmed value; the `sync` command latches the last programmed machine position (in user frame coordinates) back into the dimension word variables.

**Example:**

```
sync
fv1 = X   { read the current X axis position }
```

After `sync` latches the machine position into the dimension word variables, the current `X` axis position (in user frame coordinates) is read into `fv1`.

**See Also:** `A`, `C`, `sync`

### `xil`

Bit (boolean) access to the unique input logical variables.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | boolean array [0-511]     |
| **Access Modifier** | PLC                       |
| **Scope**           | CNC                       |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |

**Description:**

Bit (boolean) access to the unique input logical variables; `xil` is an alias for `xilb`. `xil5` and `xilb5` access the same unique input logical boolean.

**Example:**

```
bv0 = xil5   { read xil 5 }
```

Reads the value of `xil5` into `bv0`.

**See Also:** `xilb`, `xili`, `xol`

### `xilb`

Unique input logical boolean variables.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | boolean array [0-511]     |
| **Access Modifier** | PLC                       |
| **Scope**           | CNC                       |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |

**Description:**

Unique input logical boolean variables. These are global (CNC scope) logical inputs, indexed 0 to 511 (0 to 3999 in AMCore 1.10 or later). They may also be accessed by the bit alias `xil`.

**Example:**

```
bv0 = xilb5   { read xilb 5 }
```

Reads the value of `xilb5` into `bv0`.

**See Also:** `xil`, `xili`, `xilf`, `xolb`

### `xilf`

Unique input logical float variables.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | float array [0-47]        |
| **Access Modifier** | PLC                       |
| **Scope**           | CNC                       |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |

**Description:**

Unique input logical float variables, indexed 0 to 47 (0 to 499 in AMCore 1.10 or later).

**Example:**

```
fv0 = xilf5   { read xilf 5 }
```

Reads the value of `xilf5` into `fv0`.

**See Also:** `xilb`, `xili`

### `xili`

Unique input logical integer variables.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | integer array [0-29]      |
| **Access Modifier** | PLC                       |
| **Scope**           | CNC                       |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |

**Description:**

Unique input logical integer variables, indexed 0 to 29 (0 to 199 in AMCore 1.10 or later).

**Example:**

```
iv0 = xili5   { read xili 5 }
```

Reads the value of `xili5` into `iv0`.

**See Also:** `xilb`, `xilf`

### `xol`

Bit (boolean) access to the unique output logical variables.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | boolean array [0-1099]    |
| **Access Modifier** | PLC                       |
| **Scope**           | CNC                       |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |

**Description:**

Bit (boolean) access to the unique output logical variables; `xol` is an alias for `xolb`. `xol5` and `xolb5` access the same unique output logical boolean.

**Example:**

```
xol5 = on   { drive xol 5 }
```

Sets `xol5` to `on`.

**See Also:** `xolb`, `xoli`, `xil`

### `xolb`

Unique output logical boolean variables.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | boolean array [0-1099]    |
| **Access Modifier** | PLC                       |
| **Scope**           | CNC                       |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |

**Description:**

Unique output logical boolean variables. These are global (CNC scope) logical outputs, indexed 0 to 1099 (0 to 3999 in AMCore 1.10 or later). They may also be accessed by the bit alias `xol`.

**Example:**

```
xolb5 = on   { drive xolb 5 }
```

Sets `xolb5` to `on`.

**See Also:** `xol`, `xoli`, `xolf`, `xilb`

### `xolf`

Unique output logical float variables.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | float array [0-31]        |
| **Access Modifier** | PLC                       |
| **Scope**           | CNC                       |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |

**Description:**

Unique output logical float variables, indexed 0 to 31 (0 to 499 in AMCore 1.10 or later).

**Example:**

```
xolf5 = 1.5   { set xolf 5 }
```

Sets `xolf5` to `1.5`.

**See Also:** `xolb`, `xoli`

### `xoli`

Unique output logical integer variables.

| Property            | Value                     |
| ------------------- | ------------------------- |
| **Type**            | integer array [0-4]       |
| **Access Modifier** | PLC                       |
| **Scope**           | CNC                       |
| **Life Time**       | AMCore Runtime (Volatile) |
| **Lookahead**       | No                        |

**Description:**

Unique output logical integer variables, indexed 0 to 4 (0 to 199 in AMCore 1.10 or later).

**Example:**

```
xoli5 = 42   { set xoli 5 }
```

Sets `xoli5` to `42`.

**See Also:** `xolb`, `xolf`

### `Y`

Programmed dimension word 'Y' value or current command position of `Y` axis in user frame coordinates.

| Property            | Value                                                                                                          |
| ------------------- | -------------------------------------------------------------------------------------------------------------- |
| **Type**            | float                                                                                                          |
| **Access Modifier** | PPP                                                                                                            |
| **Scope**           | PPP                                                                                                            |
| **Life Time**       | AMCore Runtime (Volatile)                                                                                      |
| **Lookahead**       | No                                                                                                             |
| **Units**           | Dimensionless or mm or inches or degrees, depending on current modal conditions and linear/rotary axis status. |

**Description:**

Programmed dimension word 'Y' value or current command position of `Y` axis in user frame coordinates. Dimension words are also accessible as variables, where the variable takes on its last programmed value; the `sync` command latches the last programmed machine position (in user frame coordinates) back into the dimension word variables.

**Example:**

```
sync
fv1 = Y   { read the current Y axis position }
```

After `sync` latches the machine position into the dimension word variables, the current `Y` axis position (in user frame coordinates) is read into `fv1`.

**See Also:** `A`, `C`, `sync`

### `Z`

Programmed dimension word 'Z' value or current command position of `Z` axis in user frame coordinates.

| Property            | Value                                                                                                          |
| ------------------- | -------------------------------------------------------------------------------------------------------------- |
| **Type**            | float                                                                                                          |
| **Access Modifier** | PPP                                                                                                            |
| **Scope**           | PPP                                                                                                            |
| **Life Time**       | AMCore Runtime (Volatile)                                                                                      |
| **Lookahead**       | No                                                                                                             |
| **Units**           | Dimensionless or mm or inches or degrees, depending on current modal conditions and linear/rotary axis status. |

**Description:**

Programmed dimension word 'Z' value or current command position of `Z` axis in user frame coordinates. Dimension words are also accessible as variables, where the variable takes on its last programmed value; the `sync` command latches the last programmed machine position (in user frame coordinates) back into the dimension word variables.

**Example:**

```
sync
fv1 = Z   { read the current Z axis position }
```

After `sync` latches the machine position into the dimension word variables, the current `Z` axis position (in user frame coordinates) is read into `fv1`.

**See Also:** `A`, `C`, `sync`

## Footnotes

[^49]: Note that during power up initialisation sequences, some of these variables will be changed from their default values.

[^50]: Only used for some special variables.
