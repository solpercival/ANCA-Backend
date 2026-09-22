# Appendix A1: TCG Functions

This appendix documents EPPL functions specific to Tool and Cutter Grinder (TCG) applications. These are only available on machines configured for tool grinding. For TCG constants, see Appendix A2.

---


### `programmable_pressure_fitted`

Returns the value of the coolant type configuration parameter.

**Syntax:**

```
integer programmable_pressure_fitted()
```

**Description:**

Returns the value of the configuration parameter *coolant_type. If the parameter is not defined, a PPI execution error is raised.

**Returns:**

| Type    | Description                                          |
| ------- | ---------------------------------------------------- |
| integer | The value of the *coolant_type configuration parameter |

**Example:**

```
if (programmable_pressure_fitted())
   set_pressure(50.0)
endif
```

Checks whether programmable coolant pressure is configured and, if so, sets the pressure to 50 in the configured units.

**See Also:** `set_pressure`

### `reset_nomrad_bc`

Resets `B` and `C` nominal radii to their previous values.

**Syntax:**

```
reset_nomrad_bc
```

**Description:**

Resets the `B` and `C` axes to their previous nominal radii, restoring the values that were in effect prior to the last `set_nomrad_bc` call.

**Example:**

```
G67 B70 C50
set_nomrad_bc(40)
...
reset_nomrad_bc
```

The first command sets the `nomrad` for `B` axis to 70 units and `C` axis to 50 units. Then it temporarily overrides the `B` and `C` nominal radii with `set_nomrad_bc` to 40 units. After processing other code, `reset_nomrad_bc` restores the nominal radii to 70 and 40 units respectively.

**See Also:** `set_nomrad_bc`

### `set_nomrad_bc`

Temporarily overrides nominal radius for `B` and `C` axes.

**Syntax:**

```
set_nomrad_bc(float radius)
```

**Description:**

Temporarily overrides `B` and `C` nominal radii. It takes as an argument the desired override radius in units. When running in metric mode, the unit for `set_nomrad_bc()` is millimetre and in imperial mode, the unit is inch. When the combined motion is finished, the function `reset_nomrad_bc` should be used to reset the `B` and `C` to their previous radii. Note that radii smaller than 2.0mm will be detected as a potential problem, and an error will be issued to the user.

**Parameters:**

| Parameter | Type  | Description                                          |
| --------- | ----- | ---------------------------------------------------- |
| radius    | float | The desired override radius in units (mm or inch)    |

**Example:**

```
G67 B70                { Sets the nominal radius of the B axis to 70 units }
set_nomrad_bc(40)      { Sets the nominal radius of B and C to 40 units }
...
reset_nomrad_bc        { Resets to previous radii }
```

Sets the `B` axis nominal radius to 70 units with `G67`, temporarily overrides both `B` and `C` nominal radii to 40 units for the combined motion, then restores the previous radii with `reset_nomrad_bc`.

**See Also:** `reset_nomrad_bc`

### `set_pressure`

Sets the coolant pressure to a specified value.

**Syntax:**

```
set_pressure(float target_pressure)
```

**Description:**

Set the pressure to the value specified. The units of pressure (KPA, BAR or PSI) are specified by the configuration parameter *pressure_units. These functions are typically used to control coolant pressure in grinding applications.

**Parameters:**

| Parameter       | Type  | Description                                          |
| --------------- | ----- | ---------------------------------------------------- |
| target_pressure | float | The target pressure value in configured units        |

**Example:**

```
set_pressure(50.0)
```

Sets the coolant pressure to 50 in the units.

**See Also:** `programmable_pressure_fitted`

### `tg_end_gash_ext_tool_basic`

Transforms a grinding position specified in tool coordinates into the corresponding machine axis values, for gashing the end face of the tool, with added flexibility via a profile tangent input.

**Syntax:**

```
integer tg_end_gash_ext_tool_basic(float axis_vals[], float r, float theta, float l, float prof_tangent, float rake, float dish, float face, float del_x, float del_y, float del_z, float edge_tangent, float pri, float oblique, integer c_cl_flag, float c_clearance, float toroid_rad)
```

**Description:**

Transforms a grinding position p, specified in tool coordinates, into the corresponding machine axis values for gashing the end face. This is the extended form of `tg_end_gash_tool_basic`, adding a profile tangent input for greater flexibility. The six calculated axis values (X, Y, Z, A, B, C) are written into the axis_vals array passed as the first argument. The function returns `tg_set_a` if a singularity occurred while calculating the `A` axis value, or `tg_ok` otherwise.

**Parameters:**

| Parameter    | Type        | Description                                                                                                                                                                                                                                           |
| ------------ | ----------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| axis_vals    | float array | Output array receiving the calculated machine axis values X, Y, Z, A, B, C.                                                                                                                                                                           |
| r            | float       | Tool radius at the start position at the edge of the end face.                                                                                                                                                                                        |
| theta        | float       | Angle from the reference `Y` axis to the start position at the edge of the end face.                                                                                                                                                                    |
| l            | float       | Distance along the tool to the start position.                                                                                                                                                                                                        |
| prof_tangent | float       | Profile tangent angle; the rotation angle to align with the end face (90 degrees for an end face).                                                                                                                                                    |
| rake         | float       | Rake angle.                                                                                                                                                                                                                                           |
| dish         | float       | Dish angle.                                                                                                                                                                                                                                           |
| face         | float       | Face angle.                                                                                                                                                                                                                                           |
| del_x        | float       | Offset along the end face in X.                                                                                                                                                                                                                       |
| del_y        | float       | Offset along the end face in Y.                                                                                                                                                                                                                       |
| del_z        | float       | Offset along the end face in Z.                                                                                                                                                                                                                       |
| edge_tangent | float       | Angle of the cutting edge with respect to the edge defined by rake and dish.                                                                                                                                                                          |
| pri          | float       | Primary relief angle.                                                                                                                                                                                                                                 |
| oblique      | float       | Oblique angle.                                                                                                                                                                                                                                        |
| c_cl_flag    | integer     | Bit-field selecting solution options: `tg_def_c`/`tg_def_cl` (fix C or define clearance), `tg_right_hx`/`tg_left_hx` (helix hand), `tg_right_cut`/`tg_left_cut` (cut hand), `tg_bk_surf`/`tg_ft_surf` (back or front surface) and `tg_std_c`/`tg_non_std_c` (C quadrant). |
| c_clearance  | float       | Either the `C` axis value or the clearance, depending on c_cl_flag.                                                                                                                                                                                     |
| toroid_rad   | float       | Radius of the toroid defining the wheel edge.                                                                                                                                                                                                         |

**Returns:**

| Type    | Description                                                                             |
| ------- | --------------------------------------------------------------------------------------- |
| integer | `tg_set_a` if a singularity occurred while calculating the `A` axis value, otherwise `tg_ok`. |

**Example:**

```
result = tg_end_gash_ext_tool_basic(axis_vals, 25.0, 0.0, 10.0, 90.0, 5.0, 2.0, 90.0, 0.0, 0.0, 0.0, 0.0, 8.0, 5.0, tg_def_cl, 1.5, 3.0)
```

With axis_vals a six-element float array and prof_tangent set to 90 degrees for an end face, calculates the X, Y, Z, A, B, C machine axis values for gashing the end face and stores them in axis_vals. result is `tg_ok` unless an `A` axis singularity occurs, in which case it is `tg_set_a`.

**See Also:** `tg_end_gash_tool_basic`, `tg_end_tert_ext_tool_basic`, `tg_end_pri_tool_basic`, `tg_def_c`, `tg_def_cl`, `tg_right_hx`, `tg_left_hx`, `tg_right_cut`, `tg_left_cut`, `tg_bk_surf`, `tg_ft_surf`, `tg_std_c`, `tg_non_std_c`, `tg_ok`, `tg_set_a`

### `tg_end_gash_tool_basic`

Transforms a grinding position specified in tool coordinates into the corresponding machine axis values, for gashing the end face of the tool.

**Syntax:**

```
integer tg_end_gash_tool_basic(float axis_vals[], float r, float theta, float l, float rake, float dish, float face, float del_x, float del_y, float del_z, float edge_tangent, float pri, float oblique, integer c_cl_flag, float c_clearance, float toroid_rad)
```

**Description:**

Transforms a grinding position p, specified in tool coordinates, into the corresponding machine axis values for gashing the end face. The six calculated axis values (X, Y, Z, A, B, C) are written into the axis_vals array passed as the first argument. The function returns `tg_set_a` if a singularity occurred while calculating the `A` axis value, or `tg_ok` otherwise.

**Parameters:**

| Parameter    | Type        | Description                                                                                                                                                                                                                                           |
| ------------ | ----------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| axis_vals    | float array | Output array receiving the calculated machine axis values X, Y, Z, A, B, C.                                                                                                                                                                           |
| r            | float       | Tool radius at the start position at the edge of the end face.                                                                                                                                                                                        |
| theta        | float       | Angle from the reference `Y` axis to the start position at the edge of the end face.                                                                                                                                                                    |
| l            | float       | Distance along the tool to the start position.                                                                                                                                                                                                        |
| rake         | float       | Rake angle.                                                                                                                                                                                                                                           |
| dish         | float       | Dish angle.                                                                                                                                                                                                                                           |
| face         | float       | Face angle.                                                                                                                                                                                                                                           |
| del_x        | float       | Offset along the end face in X.                                                                                                                                                                                                                       |
| del_y        | float       | Offset along the end face in Y.                                                                                                                                                                                                                       |
| del_z        | float       | Offset along the end face in Z.                                                                                                                                                                                                                       |
| edge_tangent | float       | Angle of the cutting edge with respect to the edge defined by rake and dish.                                                                                                                                                                          |
| pri          | float       | Primary relief angle.                                                                                                                                                                                                                                 |
| oblique      | float       | Oblique angle.                                                                                                                                                                                                                                        |
| c_cl_flag    | integer     | Bit-field selecting solution options: `tg_def_c`/`tg_def_cl` (fix C or define clearance), `tg_right_hx`/`tg_left_hx` (helix hand), `tg_right_cut`/`tg_left_cut` (cut hand), `tg_bk_surf`/`tg_ft_surf` (back or front surface) and `tg_std_c`/`tg_non_std_c` (C quadrant). |
| c_clearance  | float       | Either the `C` axis value or the clearance, depending on c_cl_flag.                                                                                                                                                                                     |
| toroid_rad   | float       | Radius of the toroid defining the wheel edge.                                                                                                                                                                                                         |

**Returns:**

| Type    | Description                                                                             |
| ------- | --------------------------------------------------------------------------------------- |
| integer | `tg_set_a` if a singularity occurred while calculating the `A` axis value, otherwise `tg_ok`. |

**Example:**

```
result = tg_end_gash_tool_basic(axis_vals, 25.0, 0.0, 10.0, 5.0, 2.0, 90.0, 0.0, 0.0, 0.0, 0.0, 8.0, 5.0, tg_def_cl, 1.5, 3.0)
```

With axis_vals a six-element float array, calculates the X, Y, Z, A, B, C machine axis values for gashing the end face and stores them in axis_vals. result is `tg_ok` unless an `A` axis singularity occurs, in which case it is `tg_set_a`.

**See Also:** `tg_end_gash_ext_tool_basic`, `tg_end_pri_tool_basic`, `tg_end_tert_tool_basic`, `tg_def_c`, `tg_def_cl`, `tg_right_hx`, `tg_left_hx`, `tg_right_cut`, `tg_left_cut`, `tg_bk_surf`, `tg_ft_surf`, `tg_std_c`, `tg_non_std_c`, `tg_ok`, `tg_set_a`

### `tg_end_pri_tool_basic`

Transforms a grinding position specified in tool coordinates into the corresponding machine axis values, for grinding the primary relief on the end face of the tool.

**Syntax:**

```
integer tg_end_pri_tool_basic(float axis_vals[], float r, float theta, float l, float rake, float dish, float face, float del_x, float del_y, float del_z, float edge_tangent, float pri, float oblique, integer c_cl_flag, float c_clearance, float toroid_rad)
```

**Description:**

Transforms a grinding position p, specified in tool coordinates, into the corresponding machine axis values for grinding the primary relief on the end face. The six calculated axis values (X, Y, Z, A, B, C) are written into the axis_vals array passed as the first argument. The function returns `tg_set_a` if a singularity occurred while calculating the `A` axis value, or `tg_ok` otherwise.

**Parameters:**

| Parameter    | Type        | Description                                                                                                 |
| ------------ | ----------- | ----------------------------------------------------------------------------------------------------------- |
| axis_vals    | float array | Output array receiving the calculated machine axis values X, Y, Z, A, B, C.                                 |
| r            | float       | Tool radius at the start position at the edge of the end face.                                              |
| theta        | float       | Angle from the reference `Y` axis to the start position at the edge of the end face.                          |
| l            | float       | Distance along the tool to the start position.                                                              |
| rake         | float       | Rake angle.                                                                                                 |
| dish         | float       | Dish angle.                                                                                                 |
| face         | float       | Face angle.                                                                                                 |
| del_x        | float       | Offset along the end face in X.                                                                             |
| del_y        | float       | Offset along the end face in Y.                                                                             |
| del_z        | float       | Offset along the end face in Z.                                                                             |
| edge_tangent | float       | Angle of the cutting edge with respect to the edge defined by rake and dish.                                |
| pri          | float       | Primary relief angle.                                                                                       |
| oblique      | float       | Oblique angle.                                                                                              |
| c_cl_flag    | integer     | Selects how the `C` axis is resolved: `tg_def_c` to fix the `C` axis value, or `tg_def_cl` to define the clearance. |
| c_clearance  | float       | Either the `C` axis value or the clearance, depending on c_cl_flag.                                           |
| toroid_rad   | float       | Radius of the toroid defining the wheel edge.                                                               |

**Returns:**

| Type    | Description                                                                             |
| ------- | --------------------------------------------------------------------------------------- |
| integer | `tg_set_a` if a singularity occurred while calculating the `A` axis value, otherwise `tg_ok`. |

**Example:**

```
result = tg_end_pri_tool_basic(axis_vals, 25.0, 0.0, 10.0, 5.0, 2.0, 90.0, 0.0, 0.0, 0.0, 0.0, 8.0, 5.0, tg_def_cl, 1.5, 3.0)
```

With axis_vals a six-element float array, calculates the X, Y, Z, A, B, C machine axis values for a primary-relief grind on the end face and stores them in axis_vals. result is `tg_ok` unless an `A` axis singularity occurs, in which case it is `tg_set_a`.

**See Also:** `tg_end_sec_tool_basic`, `tg_end_tert_tool_basic`, `tg_end_gash_tool_basic`, `tg_pri_tool_basic`, `tg_def_c`, `tg_def_cl`, `tg_ok`, `tg_set_a`

### `tg_end_sec_tool_basic`

Transforms a grinding position specified in tool coordinates into the corresponding machine axis values, for grinding the secondary relief on the end face of the tool.

**Syntax:**

```
integer tg_end_sec_tool_basic(float axis_vals[], float r, float theta, float l, float rake, float dish, float face, float del_x, float del_y, float del_z, float edge_tangent, float pri, float pri_land, float sec, float oblique, integer c_cl_flag, float c_clearance, float toroid_rad)
```

**Description:**

Transforms a grinding position p, specified in tool coordinates, into the corresponding machine axis values for grinding the secondary relief on the end face. The six calculated axis values (X, Y, Z, A, B, C) are written into the axis_vals array passed as the first argument. The function returns `tg_set_a` if a singularity occurred while calculating the `A` axis value, or `tg_ok` otherwise.

**Parameters:**

| Parameter    | Type        | Description                                                                                                 |
| ------------ | ----------- | ----------------------------------------------------------------------------------------------------------- |
| axis_vals    | float array | Output array receiving the calculated machine axis values X, Y, Z, A, B, C.                                 |
| r            | float       | Tool radius at the start position at the edge of the end face.                                              |
| theta        | float       | Angle from the reference `Y` axis to the start position at the edge of the end face.                          |
| l            | float       | Distance along the tool to the start position.                                                              |
| rake         | float       | Rake angle.                                                                                                 |
| dish         | float       | Dish angle.                                                                                                 |
| face         | float       | Face angle.                                                                                                 |
| del_x        | float       | Offset along the end face in X.                                                                             |
| del_y        | float       | Offset along the end face in Y.                                                                             |
| del_z        | float       | Offset along the end face in Z.                                                                             |
| edge_tangent | float       | Angle of the cutting edge with respect to the edge defined by rake and dish.                                |
| pri          | float       | Primary relief angle.                                                                                       |
| pri_land     | float       | Primary land width.                                                                                         |
| sec          | float       | Secondary relief angle.                                                                                     |
| oblique      | float       | Oblique angle.                                                                                              |
| c_cl_flag    | integer     | Selects how the `C` axis is resolved: `tg_def_c` to fix the `C` axis value, or `tg_def_cl` to define the clearance. |
| c_clearance  | float       | Either the `C` axis value or the clearance, depending on c_cl_flag.                                           |
| toroid_rad   | float       | Radius of the toroid defining the wheel edge.                                                               |

**Returns:**

| Type    | Description                                                                             |
| ------- | --------------------------------------------------------------------------------------- |
| integer | `tg_set_a` if a singularity occurred while calculating the `A` axis value, otherwise `tg_ok`. |

**Example:**

```
result = tg_end_sec_tool_basic(axis_vals, 25.0, 0.0, 10.0, 5.0, 2.0, 90.0, 0.0, 0.0, 0.0, 0.0, 8.0, 1.0, 12.0, 5.0, tg_def_cl, 1.5, 3.0)
```

With axis_vals a six-element float array, calculates the X, Y, Z, A, B, C machine axis values for a secondary-relief grind on the end face and stores them in axis_vals. result is `tg_ok` unless an `A` axis singularity occurs, in which case it is `tg_set_a`.

**See Also:** `tg_end_pri_tool_basic`, `tg_end_tert_tool_basic`, `tg_end_gash_tool_basic`, `tg_sec_tool_basic`, `tg_def_c`, `tg_def_cl`, `tg_ok`, `tg_set_a`

### `tg_end_tert_ext_tool_basic`

Transforms a grinding position specified in tool coordinates into the corresponding machine axis values, for grinding the tertiary relief on the end face of the tool, with added flexibility via a profile tangent input.

**Syntax:**

```
integer tg_end_tert_ext_tool_basic(float axis_vals[], float r, float theta, float l, float prof_tangent, float rake, float dish, float face, float del_x, float del_y, float del_z, float edge_tangent, float pri, float pri_land, float sec, float sec_land, float tert, float oblique, integer c_cl_flag, float c_clearance, float toroid_rad)
```

**Description:**

Transforms a grinding position p, specified in tool coordinates, into the corresponding machine axis values for grinding the tertiary relief on the end face. This is the extended form of `tg_end_tert_tool_basic`, adding a profile tangent input for greater flexibility. The six calculated axis values (X, Y, Z, A, B, C) are written into the axis_vals array passed as the first argument. The function returns `tg_set_a` if a singularity occurred while calculating the `A` axis value, or `tg_ok` otherwise.

**Parameters:**

| Parameter    | Type        | Description                                                                                                                                                                                                                                           |
| ------------ | ----------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| axis_vals    | float array | Output array receiving the calculated machine axis values X, Y, Z, A, B, C.                                                                                                                                                                           |
| r            | float       | Tool radius at the start position at the edge of the end face.                                                                                                                                                                                        |
| theta        | float       | Angle from the reference `Y` axis to the start position at the edge of the end face.                                                                                                                                                                    |
| l            | float       | Distance along the tool to the start position.                                                                                                                                                                                                        |
| prof_tangent | float       | Profile tangent angle; the rotation angle to align with the end face (90 degrees for an end face).                                                                                                                                                    |
| rake         | float       | Rake angle.                                                                                                                                                                                                                                           |
| dish         | float       | Dish angle.                                                                                                                                                                                                                                           |
| face         | float       | Face angle.                                                                                                                                                                                                                                           |
| del_x        | float       | Offset along the end face in X.                                                                                                                                                                                                                       |
| del_y        | float       | Offset along the end face in Y.                                                                                                                                                                                                                       |
| del_z        | float       | Offset along the end face in Z.                                                                                                                                                                                                                       |
| edge_tangent | float       | Angle of the cutting edge with respect to the edge defined by rake and dish.                                                                                                                                                                          |
| pri          | float       | Primary relief angle.                                                                                                                                                                                                                                 |
| pri_land     | float       | Primary land width.                                                                                                                                                                                                                                   |
| sec          | float       | Secondary relief angle.                                                                                                                                                                                                                               |
| sec_land     | float       | Secondary land width.                                                                                                                                                                                                                                 |
| tert         | float       | Tertiary relief angle.                                                                                                                                                                                                                                |
| oblique      | float       | Oblique angle.                                                                                                                                                                                                                                        |
| c_cl_flag    | integer     | Bit-field selecting solution options: `tg_def_c`/`tg_def_cl` (fix C or define clearance), `tg_right_hx`/`tg_left_hx` (helix hand), `tg_right_cut`/`tg_left_cut` (cut hand), `tg_bk_surf`/`tg_ft_surf` (back or front surface) and `tg_std_c`/`tg_non_std_c` (C quadrant). |
| c_clearance  | float       | Either the `C` axis value or the clearance, depending on c_cl_flag.                                                                                                                                                                                     |
| toroid_rad   | float       | Radius of the toroid defining the wheel edge.                                                                                                                                                                                                         |

**Returns:**

| Type    | Description                                                                             |
| ------- | --------------------------------------------------------------------------------------- |
| integer | `tg_set_a` if a singularity occurred while calculating the `A` axis value, otherwise `tg_ok`. |

**Example:**

```
result = tg_end_tert_ext_tool_basic(axis_vals, 25.0, 0.0, 10.0, 90.0, 5.0, 2.0, 90.0, 0.0, 0.0, 0.0, 0.0, 8.0, 1.0, 12.0, 1.0, 16.0, 5.0, tg_def_cl, 1.5, 3.0)
```

With axis_vals a six-element float array and prof_tangent set to 90 degrees for an end face, calculates the X, Y, Z, A, B, C machine axis values for a tertiary-relief grind and stores them in axis_vals. result is `tg_ok` unless an `A` axis singularity occurs, in which case it is `tg_set_a`.

**See Also:** `tg_end_tert_tool_basic`, `tg_end_gash_ext_tool_basic`, `tg_end_pri_tool_basic`, `tg_tert_tool_basic`, `tg_def_c`, `tg_def_cl`, `tg_right_hx`, `tg_left_hx`, `tg_right_cut`, `tg_left_cut`, `tg_bk_surf`, `tg_ft_surf`, `tg_std_c`, `tg_non_std_c`, `tg_ok`, `tg_set_a`

### `tg_end_tert_tool_basic`

Transforms a grinding position specified in tool coordinates into the corresponding machine axis values, for grinding the tertiary relief on the end face of the tool.

**Syntax:**

```
integer tg_end_tert_tool_basic(float axis_vals[], float r, float theta, float l, float rake, float dish, float face, float del_x, float del_y, float del_z, float edge_tangent, float pri, float pri_land, float sec, float sec_land, float tert, float oblique, integer c_cl_flag, float c_clearance, float toroid_rad)
```

**Description:**

Transforms a grinding position p, specified in tool coordinates, into the corresponding machine axis values for grinding the tertiary relief on the end face. The six calculated axis values (X, Y, Z, A, B, C) are written into the axis_vals array passed as the first argument. The function returns `tg_set_a` if a singularity occurred while calculating the `A` axis value, or `tg_ok` otherwise.

**Parameters:**

| Parameter    | Type        | Description                                                                                                                                                                                                                                           |
| ------------ | ----------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| axis_vals    | float array | Output array receiving the calculated machine axis values X, Y, Z, A, B, C.                                                                                                                                                                           |
| r            | float       | Tool radius at the start position at the edge of the end face.                                                                                                                                                                                        |
| theta        | float       | Angle from the reference `Y` axis to the start position at the edge of the end face.                                                                                                                                                                    |
| l            | float       | Distance along the tool to the start position.                                                                                                                                                                                                        |
| rake         | float       | Rake angle.                                                                                                                                                                                                                                           |
| dish         | float       | Dish angle.                                                                                                                                                                                                                                           |
| face         | float       | Face angle.                                                                                                                                                                                                                                           |
| del_x        | float       | Offset along the end face in X.                                                                                                                                                                                                                       |
| del_y        | float       | Offset along the end face in Y.                                                                                                                                                                                                                       |
| del_z        | float       | Offset along the end face in Z.                                                                                                                                                                                                                       |
| edge_tangent | float       | Angle of the cutting edge with respect to the edge defined by rake and dish.                                                                                                                                                                          |
| pri          | float       | Primary relief angle.                                                                                                                                                                                                                                 |
| pri_land     | float       | Primary land width.                                                                                                                                                                                                                                   |
| sec          | float       | Secondary relief angle.                                                                                                                                                                                                                               |
| sec_land     | float       | Secondary land width.                                                                                                                                                                                                                                 |
| tert         | float       | Tertiary relief angle.                                                                                                                                                                                                                                |
| oblique      | float       | Oblique angle.                                                                                                                                                                                                                                        |
| c_cl_flag    | integer     | Bit-field selecting solution options: `tg_def_c`/`tg_def_cl` (fix C or define clearance), `tg_right_hx`/`tg_left_hx` (helix hand), `tg_right_cut`/`tg_left_cut` (cut hand), `tg_bk_surf`/`tg_ft_surf` (back or front surface) and `tg_std_c`/`tg_non_std_c` (C quadrant). |
| c_clearance  | float       | Either the `C` axis value or the clearance, depending on c_cl_flag.                                                                                                                                                                                     |
| toroid_rad   | float       | Radius of the toroid defining the wheel edge.                                                                                                                                                                                                         |

**Returns:**

| Type    | Description                                                                             |
| ------- | --------------------------------------------------------------------------------------- |
| integer | `tg_set_a` if a singularity occurred while calculating the `A` axis value, otherwise `tg_ok`. |

**Example:**

```
result = tg_end_tert_tool_basic(axis_vals, 25.0, 0.0, 10.0, 5.0, 2.0, 90.0, 0.0, 0.0, 0.0, 0.0, 8.0, 1.0, 12.0, 1.0, 16.0, 5.0, tg_def_cl, 1.5, 3.0)
```

With axis_vals a six-element float array, calculates the X, Y, Z, A, B, C machine axis values for a tertiary-relief grind on the end face and stores them in axis_vals. result is `tg_ok` unless an `A` axis singularity occurs, in which case it is `tg_set_a`.

**See Also:** `tg_end_pri_tool_basic`, `tg_end_sec_tool_basic`, `tg_end_tert_ext_tool_basic`, `tg_tert_tool_basic`, `tg_def_c`, `tg_def_cl`, `tg_right_hx`, `tg_left_hx`, `tg_right_cut`, `tg_left_cut`, `tg_bk_surf`, `tg_ft_surf`, `tg_std_c`, `tg_non_std_c`, `tg_ok`, `tg_set_a`

### `tg_fl_oblique`

Calculates the oblique angle for a specified flute depth.

**Syntax:**

```
tg_fl_oblique(float &obl_p, float r, float outer_taper, float core_taper, float depth, float x, float helix, float hook, float wh_rad, float toroid_rad, float clearance, integer lh_cut, integer lh_helix)
```

**Description:**

This function calculates the oblique angle to be supplied to `tg_fl_tool_basic()` in order to achieve a specified flute depth. Note that this function uses an iterative procedure and consequently takes about a hundred milliseconds to run.

The tool is described by two cones: the outer cone defined by the outer taper angle on the cutting edge and the core cone defined by the core taper. The approach used is to approximate the helix in the region of interest by an ellipse. Have outer ellipse (on cutting edge) and core ellipse. The problem becomes a two dimensional one in the plane of these ellipses. Have to find the position of the centre of a circle (wheel) such that it passes through the grind point P (on outer ellipse) and is tangent with core ellipse.

**Parameters:**

| Parameter   | Type    | Description                                          |
| ----------- | ------- | ---------------------------------------------------- |
| obl_p       | float   | Calculated oblique (output)                          |
| r           | float   | Tool radius at x = 0                                |
| outer_taper | float   | Taper angle at cutting edge                          |
| core_taper  | float   | Taper angle of core                                  |
| depth       | float   | Required flute depth at x = 0                        |
| x           | float   | x coordinate for which the oblique angle is to be calculated. Normally end of tool is x = 0 |
| helix       | float   | Helix angle                                          |
| hook        | float   | Hook angle (normal to axis of tool not cut edge)     |
| wh_rad      | float   | Radius of grinding wheel                             |
| toroid_rad  | float   | Toroid radius of grinding wheel                      |
| clearance   | float   | The clearance angle when grinding                    |
| lh_cut      | integer | Signals right or left hand cut (0 for right hand cut, 1 for left hand cut) |
| lh_helix    | integer | Signals right or left hand lead (0 for right hand helix, 1 for left hand helix) |

**Example:**

```
tg_fl_oblique(&obl_p, 25.0, 5.0, 3.0, 2.0, 0.0, 30.0, 5.0, 75.0, 3.0, 8.0, 0, 0)
result = tg_fl_tool_basic(axis_vals, 25.0, 0.0, 10.0, 5.0, 30.0, 5.0, obl_p, tg_def_cl, 1.5, 3.0)
```

Calculates the oblique angle `obl_p` needed to achieve a 2 unit flute depth at the end of the tool (x = 0), then passes that oblique angle to `tg_fl_tool_basic` to compute the machine axis values for the flute grind.

**See Also:** `tg_fl_tool_basic`

### `tg_fl_tool_basic`

Transforms a grinding position specified in tool coordinates into the corresponding machine axis values, for flute grinding.

**Syntax:**

```
integer tg_fl_tool_basic(float axis_vals[], float r, float theta, float l, float taper, float helix, float hook, float oblique, integer flag, float c_clearance, float toroid_rad)
```

**Description:**

Transforms a grinding position p, specified in tool coordinates, into the corresponding machine axis values for flute grinding. The six calculated axis values (X, Y, Z, A, B, C) are written into the axis_vals array passed as the first argument. The function returns `tg_set_a` if a singularity occurred while calculating the `A` axis value, or `tg_ok` otherwise.

**Parameters:**

| Parameter   | Type        | Description                                                                                                                                                                                                                                           |
| ----------- | ----------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| axis_vals   | float array | Output array receiving the calculated machine axis values X, Y, Z, A, B, C.                                                                                                                                                                           |
| r           | float       | Tool radius at grinding position p.                                                                                                                                                                                                                   |
| theta       | float       | Angle from the reference `Y` axis to position p.                                                                                                                                                                                                        |
| l           | float       | Distance along the tool.                                                                                                                                                                                                                              |
| taper       | float       | Taper of the tool.                                                                                                                                                                                                                                    |
| helix       | float       | Helix angle of the tool.                                                                                                                                                                                                                              |
| hook        | float       | Hook angle of the tool, defined normal to the cutting edge rather than the tool axis.                                                                                                                                                                 |
| oblique     | float       | Oblique angle.                                                                                                                                                                                                                                        |
| flag        | integer     | Bit-field selecting solution options: `tg_def_c`/`tg_def_cl` (fix C or define clearance), `tg_right_hx`/`tg_left_hx` (helix hand), `tg_right_cut`/`tg_left_cut` (cut hand), `tg_bk_surf`/`tg_ft_surf` (back or front surface) and `tg_std_c`/`tg_non_std_c` (C quadrant). |
| c_clearance | float       | Either the `C` axis value or the clearance, depending on flag.                                                                                                                                                                                          |
| toroid_rad  | float       | Radius of the toroid defining the wheel edge.                                                                                                                                                                                                         |

**Returns:**

| Type    | Description                                                                             |
| ------- | --------------------------------------------------------------------------------------- |
| integer | `tg_set_a` if a singularity occurred while calculating the `A` axis value, otherwise `tg_ok`. |

**Example:**

```
result = tg_fl_tool_basic(axis_vals, 25.0, 0.0, 10.0, 2.0, 30.0, 5.0, 5.0, tg_def_cl, 1.5, 3.0)
```

With axis_vals a six-element float array, calculates the X, Y, Z, A, B, C machine axis values for a flute grind (30 degree helix, 5 degree hook) and stores them in axis_vals. result is `tg_ok` unless an `A` axis singularity occurs, in which case it is `tg_set_a`.

**See Also:** `tg_pri_tool_basic`, `tg_radial_edge_hook`, `tg_fl_oblique`, `tg_def_c`, `tg_def_cl`, `tg_right_hx`, `tg_left_hx`, `tg_right_cut`, `tg_left_cut`, `tg_bk_surf`, `tg_ft_surf`, `tg_std_c`, `tg_non_std_c`, `tg_ok`, `tg_set_a`

### `tg_g14`

Calculates the machine axis values for a TG4 primary grind without a radial land.

**Syntax:**

```
tg_g14(float inputs[], float outputs[], integer flag, float static_inputs[])
```

**Description:**

Implements the TG4 G14 (primary grinding) operation. It calculates the grinding-path machine axis values from the supplied input coordinates and static grinding parameters, and writes the calculated axis values (X, Y, Z, A, plus B when `tg_eff` is set) into the outputs array. This variant does not apply a radial land.

**Parameters:**

| Parameter     | Type        | Description                                                                                                                         |
| ------------- | ----------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| inputs        | float array | Input array of grinding-point values, ordered X, Y, Z, A and then further values depending on the options selected in flag.         |
| outputs       | float array | Output array receiving the calculated axis values, ordered X, Y, Z, A (plus B when `tg_eff` is set).                                  |
| flag          | integer     | Option flag; an ORed combination of `tg_e0`, `tg_e1`, `tg_e2`, `tg_e10`, `tg_e11`, `tg_e12`, `tg_r1`, `tg_c1` and `tg_eff` (or `tg_no_flags` for none). |
| static_inputs | float array | Static grinding inputs, ordered: wheel diameter, primary relief, toroid diameter, secondary relief, pivot angle, land width.        |

**Example:**

```
tg_g14(inputs, outputs, tg_no_flags, static_inputs)
```

With inputs, outputs and static_inputs as float arrays, calculates the TG4 primary-grind axis values (X, Y, Z, A) and stores them in outputs. `tg_no_flags` selects no optional behaviour.

**See Also:** `tg_g15`, `tg_g14a`, `tg_g15a`, `tg_e0`, `tg_e1`, `tg_e2`, `tg_e10`, `tg_e11`, `tg_e12`, `tg_r1`, `tg_c1`, `tg_eff`, `tg_no_flags`

### `tg_g14a`

Calculates the machine axis values for a TG4 primary grind with a radial land.

**Syntax:**

```
tg_g14a(float inputs[], float outputs[], integer flag, float static_inputs[], integer no_of_grd_input)
```

**Description:**

Implements the TG4 G14A (primary grinding) operation. It behaves as `tg_g14` but additionally applies a radial land, supplied as an extra static input. The number of static inputs is given by no_of_grd_input, which must exceed the base count so that the radial-land value is present. The calculated axis values (X, Y, Z, A, plus B when `tg_eff` is set) are written into the outputs array.

**Parameters:**

| Parameter       | Type        | Description                                                                                                                               |
| --------------- | ----------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| inputs          | float array | Input array of grinding-point values, ordered X, Y, Z, A and then further values depending on the options selected in flag.               |
| outputs         | float array | Output array receiving the calculated axis values, ordered X, Y, Z, A (plus B when `tg_eff` is set).                                        |
| flag            | integer     | Option flag; an ORed combination of `tg_e0`, `tg_e1`, `tg_e2`, `tg_e10`, `tg_e11`, `tg_e12`, `tg_r1`, `tg_c1` and `tg_eff` (or `tg_no_flags` for none).       |
| static_inputs   | float array | Static grinding inputs, ordered: wheel diameter, primary relief, toroid diameter, secondary relief, pivot angle, land width, radial land. |
| no_of_grd_input | integer     | The number of static inputs supplied; must exceed the base count so that the radial-land value is present.                                |

**Example:**

```
tg_g14a(inputs, outputs, tg_no_flags, static_inputs, 7)
```

As `tg_g14` but applies a radial land: with seven static inputs supplied (no_of_grd_input = 7), calculates the TG4 primary-grind axis values (X, Y, Z, A) and stores them in outputs.

**See Also:** `tg_g14`, `tg_g15`, `tg_g15a`, `tg_e0`, `tg_e1`, `tg_e2`, `tg_e10`, `tg_e11`, `tg_e12`, `tg_r1`, `tg_c1`, `tg_eff`, `tg_no_flags`

### `tg_g15`

Calculates the machine axis values for a TG4 secondary grind without a radial land.

**Syntax:**

```
tg_g15(float inputs[], float outputs[], integer flag, float static_inputs[])
```

**Description:**

Implements the TG4 G15 (secondary grinding) operation. It calculates the grinding-path machine axis values from the supplied input coordinates and static grinding parameters, applying the land width taken from the static inputs, and writes the calculated axis values (X, Y, Z, A, plus B when `tg_eff` is set) into the outputs array. This variant does not apply a radial land.

**Parameters:**

| Parameter     | Type        | Description                                                                                                                         |
| ------------- | ----------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| inputs        | float array | Input array of grinding-point values, ordered X, Y, Z, A and then further values depending on the options selected in flag.         |
| outputs       | float array | Output array receiving the calculated axis values, ordered X, Y, Z, A (plus B when `tg_eff` is set).                                  |
| flag          | integer     | Option flag; an ORed combination of `tg_e0`, `tg_e1`, `tg_e2`, `tg_e10`, `tg_e11`, `tg_e12`, `tg_r1`, `tg_c1` and `tg_eff` (or `tg_no_flags` for none). |
| static_inputs | float array | Static grinding inputs, ordered: wheel diameter, primary relief, toroid diameter, secondary relief, pivot angle, land width.        |

**Example:**

```
tg_g15(inputs, outputs, tg_no_flags, static_inputs)
```

With inputs, outputs and static_inputs as float arrays, calculates the TG4 secondary-grind axis values (X, Y, Z, A) and stores them in outputs. `tg_no_flags` selects no optional behaviour.

**See Also:** `tg_g14`, `tg_g14a`, `tg_g15a`, `tg_e0`, `tg_e1`, `tg_e2`, `tg_e10`, `tg_e11`, `tg_e12`, `tg_r1`, `tg_c1`, `tg_eff`, `tg_no_flags`

### `tg_g15a`

Calculates the machine axis values for a TG4 secondary grind with a radial land.

**Syntax:**

```
tg_g15a(float inputs[], float outputs[], integer flag, float static_inputs[], integer no_of_grd_input)
```

**Description:**

Implements the TG4 G15A (secondary grinding) operation. It behaves as `tg_g15` but additionally applies a radial land, supplied as an extra static input, and applies the land width taken from the static inputs. The number of static inputs is given by no_of_grd_input, which must exceed the base count so that the radial-land value is present. The calculated axis values (X, Y, Z, A, plus B when `tg_eff` is set) are written into the outputs array.

**Parameters:**

| Parameter       | Type        | Description                                                                                                                               |
| --------------- | ----------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| inputs          | float array | Input array of grinding-point values, ordered X, Y, Z, A and then further values depending on the options selected in flag.               |
| outputs         | float array | Output array receiving the calculated axis values, ordered X, Y, Z, A (plus B when `tg_eff` is set).                                        |
| flag            | integer     | Option flag; an ORed combination of `tg_e0`, `tg_e1`, `tg_e2`, `tg_e10`, `tg_e11`, `tg_e12`, `tg_r1`, `tg_c1` and `tg_eff` (or `tg_no_flags` for none).       |
| static_inputs   | float array | Static grinding inputs, ordered: wheel diameter, primary relief, toroid diameter, secondary relief, pivot angle, land width, radial land. |
| no_of_grd_input | integer     | The number of static inputs supplied; must exceed the base count so that the radial-land value is present.                                |

**Example:**

```
tg_g15a(inputs, outputs, tg_no_flags, static_inputs, 7)
```

As `tg_g15` but applies a radial land: with seven static inputs supplied (no_of_grd_input = 7), calculates the TG4 secondary-grind axis values (X, Y, Z, A) and stores them in outputs.

**See Also:** `tg_g14`, `tg_g15`, `tg_g14a`, `tg_e0`, `tg_e1`, `tg_e2`, `tg_e10`, `tg_e11`, `tg_e12`, `tg_r1`, `tg_c1`, `tg_eff`, `tg_no_flags`

### `tg_pri_tool_basic`

Transforms a grinding position specified in tool coordinates into the corresponding machine axis values, for grinding the primary relief on the periphery of the tool.

**Syntax:**

```
integer tg_pri_tool_basic(float axis_vals[], float r, float theta, float l, float taper, float rad_land, float pri, float oblique, integer c_cl_flag, float c_clearance, float toroid_rad)
```

**Description:**

Transforms a grinding position p, specified in tool coordinates, into the corresponding machine axis values for grinding the primary relief. The six calculated axis values (X, Y, Z, A, B, C) are written into the axis_vals array passed as the first argument. The function returns `tg_set_a` if a singularity occurred while calculating the `A` axis value, or `tg_ok` otherwise.

**Parameters:**

| Parameter   | Type        | Description                                                                                                 |
| ----------- | ----------- | ----------------------------------------------------------------------------------------------------------- |
| axis_vals   | float array | Output array receiving the calculated machine axis values X, Y, Z, A, B, C.                                 |
| r           | float       | Tool radius at grinding position p.                                                                         |
| theta       | float       | Angle from the reference `Y` axis to position p.                                                              |
| l           | float       | Distance along the tool.                                                                                    |
| taper       | float       | Taper of the tool.                                                                                          |
| rad_land    | float       | Angular width of the radial land.                                                                           |
| pri         | float       | Primary relief angle.                                                                                       |
| oblique     | float       | Oblique angle.                                                                                              |
| c_cl_flag   | integer     | Selects how the `C` axis is resolved: `tg_def_c` to fix the `C` axis value, or `tg_def_cl` to define the clearance. |
| c_clearance | float       | Either the `C` axis value or the clearance, depending on c_cl_flag.                                           |
| toroid_rad  | float       | Radius of the toroid defining the wheel edge.                                                               |

**Returns:**

| Type    | Description                                                                             |
| ------- | --------------------------------------------------------------------------------------- |
| integer | `tg_set_a` if a singularity occurred while calculating the `A` axis value, otherwise `tg_ok`. |

**Example:**

```
result = tg_pri_tool_basic(axis_vals, 25.0, 0.0, 10.0, 2.0, 0.0, 8.0, 5.0, tg_def_cl, 1.5, 3.0)
```

With axis_vals a six-element float array, calculates the X, Y, Z, A, B, C machine axis values for a primary-relief grind and stores them in axis_vals. `tg_def_cl` selects clearance definition. result is `tg_ok` unless an `A` axis singularity occurs, in which case it is `tg_set_a`.

**See Also:** `tg_sec_tool_basic`, `tg_tert_tool_basic`, `tg_fl_tool_basic`, `tg_fl_oblique`, `tg_def_c`, `tg_def_cl`, `tg_ok`, `tg_set_a`

### `tg_radial_edge_hook`

Converts a hook angle defined perpendicular to the tool axis (radial hook) into the equivalent hook angle perpendicular to the cutting edge (edge hook).

**Syntax:**

```
float tg_radial_edge_hook(float radial_hook, float taper, float helix)
```

**Description:**

Transforms the hook angle measured perpendicular to the tool axis (the radial hook) into the corresponding hook angle measured perpendicular to the tool cutting edge (the edge hook), and returns that edge hook angle.

**Parameters:**

| Parameter   | Type  | Description                                         |
| ----------- | ----- | --------------------------------------------------- |
| radial_hook | float | Hook angle measured perpendicular to the tool axis. |
| taper       | float | Taper of the tool.                                  |
| helix       | float | Helix angle of the tool.                            |

**Returns:**

| Type  | Description                                                            |
| ----- | ---------------------------------------------------------------------- |
| float | The hook angle measured perpendicular to the cutting edge (edge hook). |

**Example:**

```
edge_hook = tg_radial_edge_hook(15.0, 5.0, 30.0)
```

Converts a 15 degree radial hook into the equivalent edge hook for a tool with a 5 degree taper and a 30 degree helix, storing the result in edge_hook.

**See Also:** `tg_fl_tool_basic`, `tg_fl_oblique`

### `tg_sec_tool_basic`

Transforms a grinding position specified in tool coordinates into the corresponding machine axis values, for grinding the secondary relief on the periphery of the tool.

**Syntax:**

```
integer tg_sec_tool_basic(float axis_vals[], float r, float theta, float l, float taper, float rad_land, float pri, float pri_land, float sec, float oblique, integer c_cl_flag, float c_clearance, float toroid_rad)
```

**Description:**

Transforms a grinding position p, specified in tool coordinates, into the corresponding machine axis values for grinding the secondary relief. The six calculated axis values (X, Y, Z, A, B, C) are written into the axis_vals array passed as the first argument. The function returns `tg_set_a` if a singularity occurred while calculating the `A` axis value, or `tg_ok` otherwise.

**Parameters:**

| Parameter   | Type        | Description                                                                                                 |
| ----------- | ----------- | ----------------------------------------------------------------------------------------------------------- |
| axis_vals   | float array | Output array receiving the calculated machine axis values X, Y, Z, A, B, C.                                 |
| r           | float       | Tool radius at grinding position p.                                                                         |
| theta       | float       | Angle from the reference `Y` axis to position p.                                                              |
| l           | float       | Distance along the tool.                                                                                    |
| taper       | float       | Taper of the tool.                                                                                          |
| rad_land    | float       | Angular width of the radial land.                                                                           |
| pri         | float       | Primary relief angle.                                                                                       |
| pri_land    | float       | Primary land width.                                                                                         |
| sec         | float       | Secondary relief angle.                                                                                     |
| oblique     | float       | Oblique angle.                                                                                              |
| c_cl_flag   | integer     | Selects how the `C` axis is resolved: `tg_def_c` to fix the `C` axis value, or `tg_def_cl` to define the clearance. |
| c_clearance | float       | Either the `C` axis value or the clearance, depending on c_cl_flag.                                           |
| toroid_rad  | float       | Radius of the toroid defining the wheel edge.                                                               |

**Returns:**

| Type    | Description                                                                             |
| ------- | --------------------------------------------------------------------------------------- |
| integer | `tg_set_a` if a singularity occurred while calculating the `A` axis value, otherwise `tg_ok`. |

**Example:**

```
result = tg_sec_tool_basic(axis_vals, 25.0, 0.0, 10.0, 2.0, 0.0, 8.0, 1.0, 12.0, 5.0, tg_def_cl, 1.5, 3.0)
```

With axis_vals a six-element float array, calculates the X, Y, Z, A, B, C machine axis values for a secondary-relief grind and stores them in axis_vals. result is `tg_ok` unless an `A` axis singularity occurs, in which case it is `tg_set_a`.

**See Also:** `tg_pri_tool_basic`, `tg_tert_tool_basic`, `tg_fl_tool_basic`, `tg_fl_oblique`, `tg_def_c`, `tg_def_cl`, `tg_ok`, `tg_set_a`

### `tg_tert_tool_basic`

Transforms a grinding position specified in tool coordinates into the corresponding machine axis values, for grinding the tertiary relief on the periphery of the tool.

**Syntax:**

```
integer tg_tert_tool_basic(float axis_vals[], float r, float theta, float l, float taper, float rad_land, float pri, float pri_land, float sec, float sec_land, float tert, float oblique, integer c_cl_flag, float c_clearance, float toroid_rad)
```

**Description:**

Transforms a grinding position p, specified in tool coordinates, into the corresponding machine axis values for grinding the tertiary relief. The six calculated axis values (X, Y, Z, A, B, C) are written into the axis_vals array passed as the first argument. The function returns `tg_set_a` if a singularity occurred while calculating the `A` axis value, or `tg_ok` otherwise.

**Parameters:**

| Parameter   | Type        | Description                                                                                                                                                                                                                                           |
| ----------- | ----------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| axis_vals   | float array | Output array receiving the calculated machine axis values X, Y, Z, A, B, C.                                                                                                                                                                           |
| r           | float       | Tool radius at grinding position p.                                                                                                                                                                                                                   |
| theta       | float       | Angle from the reference `Y` axis to position p.                                                                                                                                                                                                        |
| l           | float       | Distance along the tool.                                                                                                                                                                                                                              |
| taper       | float       | Taper of the tool.                                                                                                                                                                                                                                    |
| rad_land    | float       | Angular width of the radial land.                                                                                                                                                                                                                     |
| pri         | float       | Primary relief angle.                                                                                                                                                                                                                                 |
| pri_land    | float       | Primary land width.                                                                                                                                                                                                                                   |
| sec         | float       | Secondary relief angle.                                                                                                                                                                                                                               |
| sec_land    | float       | Secondary land width.                                                                                                                                                                                                                                 |
| tert        | float       | Tertiary relief angle.                                                                                                                                                                                                                                |
| oblique     | float       | Oblique angle.                                                                                                                                                                                                                                        |
| c_cl_flag   | integer     | Bit-field selecting solution options: `tg_def_c`/`tg_def_cl` (fix C or define clearance), `tg_right_hx`/`tg_left_hx` (helix hand), `tg_right_cut`/`tg_left_cut` (cut hand), `tg_bk_surf`/`tg_ft_surf` (back or front surface) and `tg_std_c`/`tg_non_std_c` (C quadrant). |
| c_clearance | float       | Either the `C` axis value or the clearance, depending on c_cl_flag.                                                                                                                                                                                     |
| toroid_rad  | float       | Radius of the toroid defining the wheel edge.                                                                                                                                                                                                         |

**Returns:**

| Type    | Description                                                                             |
| ------- | --------------------------------------------------------------------------------------- |
| integer | `tg_set_a` if a singularity occurred while calculating the `A` axis value, otherwise `tg_ok`. |

**Example:**

```
result = tg_tert_tool_basic(axis_vals, 25.0, 0.0, 10.0, 2.0, 0.0, 8.0, 1.0, 12.0, 1.0, 16.0, 5.0, tg_def_cl, 1.5, 3.0)
```

With axis_vals a six-element float array, calculates the X, Y, Z, A, B, C machine axis values for a tertiary-relief grind and stores them in axis_vals. result is `tg_ok` unless an `A` axis singularity occurs, in which case it is `tg_set_a`.

**See Also:** `tg_pri_tool_basic`, `tg_sec_tool_basic`, `tg_fl_tool_basic`, `tg_fl_oblique`, `tg_def_c`, `tg_def_cl`, `tg_right_hx`, `tg_left_hx`, `tg_right_cut`, `tg_left_cut`, `tg_bk_surf`, `tg_ft_surf`, `tg_std_c`, `tg_non_std_c`, `tg_ok`, `tg_set_a`

### `wheel`

Specifies wheel number for tool operations.

**Syntax:**

```
wheel wheel_number
```

**Description:**

Specifies the wheel number to use for tool grinding operations.

**Parameters:**

| Parameter    | Type    | Description              |
| ------------ | ------- | ------------------------ |
| wheel_number | integer | The wheel number to use  |

**Example:**

```
eff I23.2 J5.0 K4.3 wheel 3
```

Applies the effector offsets and selects wheel number 3 for the tool grinding operation.

**See Also:** `wheelselect`, `eff`

### `wheelselect`

Selects a wheel for wheel change.

**Syntax:**

```
wheelselect integer
wheelselect(expression)
```

**Description:**

Selects a particular wheel in preparation for a wheel change. Similar to `toolselect` but for grinding wheels.

**Parameters:**

| Parameter  | Type       | Description                     |
| ---------- | ---------- | ------------------------------- |
| integer    | integer    | Direct wheel number             |
| expression | expression | Indirect specification          |

**Example:**

```
wheelselect 3       { Select wheel number 3 }
```

Selects wheel number 3 in preparation for a wheel change.

**See Also:** `toolselect`, `wheel`
