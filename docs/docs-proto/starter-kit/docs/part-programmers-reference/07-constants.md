# Constants

This chapter documents EPPL built-in constants. These are predefined named values that can be used in part programs. Constants are grouped alphabetically.

## Integer Constants

### `alarm_severity_debug`

Alarm severity level: debug.

**Used by:** `alarm_trigger`

**See Also:** `alarm_severity_info`, `alarm_severity_warn`, `alarm_severity_error`, `alarm_severity_fatal`, `alarm_trigger`

### `alarm_severity_error`

Alarm severity level: error.

**Used by:** `alarm_trigger`

**See Also:** `alarm_severity_debug`, `alarm_severity_info`, `alarm_severity_warn`, `alarm_severity_fatal`, `alarm_trigger`

### `alarm_severity_fatal`

Alarm severity level: fatal.

**Used by:** `alarm_trigger`

**See Also:** `alarm_severity_debug`, `alarm_severity_info`, `alarm_severity_warn`, `alarm_severity_error`, `alarm_trigger`

### `alarm_severity_info`

Alarm severity level: informational.

**Used by:** `alarm_trigger`

**See Also:** `alarm_severity_debug`, `alarm_severity_warn`, `alarm_severity_error`, `alarm_severity_fatal`, `alarm_trigger`

### `alarm_severity_warn`

Alarm severity level: warning.

**Used by:** `alarm_trigger`

**See Also:** `alarm_severity_debug`, `alarm_severity_info`, `alarm_severity_error`, `alarm_severity_fatal`, `alarm_trigger`

### `bspline`

Spline type: B-spline.

**Used by:** `st`

**See Also:** `chord`, `uniform`, `splineon`, `st`

### `chord`

Spline type: chord-length.

**Used by:** `st`

**See Also:** `bspline`, `uniform`, `splineon`, `st`

### `crc_group`

Modal group number for cutter radius compensation.

**See Also:** `G41`, `G42`, `G40`

### `dba_common`

Database location: common.

**Used by:** `dba_put_float`, `dba_put_int`, `dba_put_string`, `dba_get_float`, `dba_get_int`, `dba_get_string`

**See Also:** `dba_gen`, `dba_mspec`, `dba_oem`, `dba_test`, `dba_user`

### `dba_gen`

Database location: general.

**Used by:** `dba_put_float`, `dba_put_int`, `dba_put_string`, `dba_get_float`, `dba_get_int`, `dba_get_string`

**See Also:** `dba_common`, `dba_mspec`, `dba_oem`, `dba_test`, `dba_user`

### `dba_mspec`

Database location: machine specification.

**Used by:** `dba_put_float`, `dba_put_int`, `dba_put_string`, `dba_get_float`, `dba_get_int`, `dba_get_string`

**See Also:** `dba_common`, `dba_gen`, `dba_oem`, `dba_test`, `dba_user`

### `dba_oem`

Database location: OEM.

**Used by:** `dba_put_float`, `dba_put_int`, `dba_put_string`, `dba_get_float`, `dba_get_int`, `dba_get_string`

**See Also:** `dba_common`, `dba_gen`, `dba_mspec`, `dba_test`, `dba_user`

### `dba_test`

Database location: test.

**Used by:** `dba_put_float`, `dba_put_int`, `dba_put_string`, `dba_get_float`, `dba_get_int`, `dba_get_string`

**See Also:** `dba_common`, `dba_gen`, `dba_mspec`, `dba_oem`, `dba_user`

### `dba_user`

Database location: user.

**Used by:** `dba_put_float`, `dba_put_int`, `dba_put_string`, `dba_get_float`, `dba_get_int`, `dba_get_string`

**See Also:** `dba_common`, `dba_gen`, `dba_mspec`, `dba_oem`, `dba_test`

### `dimension_mode_group`

Modal group number for dimension mode (`metric`/`inch`).

**See Also:** `G70`, `G71`

### `dimensions_num`

The number of axis dimensions supported by the CNC.

**Value:** `48`

**Description:**

Integer constant equal to 48, the maximum number of axis dimensions the CNC supports. It sizes the per-axis arrays and is the upper bound for one-based dimension indices, such as the index accepted by `cc_dim_programmed`.

**See Also:** `cc_dim_programmed`

### `eof`

Return value indicating that the end of file was reached during input.

**Value:** `-1`

**Used by:** `read`, `readkey`

**Description:**

Returned by the `read` and `readkey` functions when input fails because the end of the file was encountered. When `eof` is returned the data in the target variable is invalid.

**See Also:** `read_ok`, `read_error`, `read_tmout`, `read`, `readkey`

### `external_int_used`

Return code indicating that the requested external interrupt is already in use.

**Value:** `-2`

**Used by:** `extint_set_default_operation`

**Description:**

Returned by `extint_set_default_operation` when the external interrupt vector it was asked to install is already in use; the default operation is not applied. Registered from SMA_INT_USED (-2).

**See Also:** `extint_set_default_operation`, `extint_enable`, `extint_disable`

### `feedrate_units_group`

Modal group number for feedrate units.

**See Also:** `G94`, `G95`

### `interpolation_group`

Modal group number for interpolation mode.

**See Also:** `rapid`, `linear`, `arccw`, `arcacw`

### `maxint`

Maximum integer value.

**See Also:** `trunc`, `round`

### `measurement_units_group`

Modal group number for measurement units.

**See Also:** `G70`, `G71`

### `move_boundary_group`

Modal group number for move boundary mode.

### `null`

Integer constant with the value 0.

**Value:** `0`

**Description:**

General-purpose integer constant equal to 0, provided by the interpreter as a named zero.

### `pmal_start_error`

Panel Manager error code indicating that the application failed to start.

**Value:** `-35`

**Description:**

Error return code (-35) reported by the Panel Manager application layer when it fails to start.

### `probe_negative_edge`

Probe polarity value selecting falling-edge (negative) triggering.

**Value:** `0`

**Used by:** `probing_begin`, `probe_reenable`

**Description:**

Passed as the polarity argument to `probing_begin` and `probe_reenable` to select falling-edge (negative-edge) probe triggering. Equivalent to the polarity value 0.

**See Also:** `probe_positive_edge`, `probing_begin`, `probe_reenable`

### `probe_positive_edge`

Probe polarity value selecting rising-edge (positive) triggering.

**Value:** `1`

**Used by:** `probing_begin`, `probe_reenable`

**Description:**

Passed as the polarity argument to `probing_begin` and `probe_reenable` to select rising-edge (positive-edge) probe triggering. Equivalent to the polarity value 1.

**See Also:** `probe_negative_edge`, `probing_begin`, `probe_reenable`

### `query_active_probe`

Argument to `select_active_probe` that queries the currently active probe without changing it.

**Value:** `0`

**Used by:** `select_active_probe`

**Description:**

Passed to `select_active_probe` to query the currently selected probe instead of selecting a new one; the function returns the active probe number and leaves the selection unchanged. Registered from SMA_QUERY_ACTIVE_PROBE (0).

**See Also:** `select_active_probe`

### `read_error`

Return value indicating that an error occurred during input.

**Value:** `-3`

**Used by:** `read`, `readkey`

**Description:**

Returned by the `read` and `readkey` functions when an error occurs while reading. When `read_error` is returned the data in the target variable is invalid.

**See Also:** `read_ok`, `eof`, `read_tmout`, `read`, `readkey`

### `read_ok`

Return value from `read` indicating that input completed successfully.

**Value:** `0`

**Used by:** `read`

**Description:**

Returned by the `read` function when the input data has been read successfully. When `read_ok` is returned the value stored in the target variable is valid.

**See Also:** `eof`, `read_error`, `read_tmout`, `read`, `readkey`

### `read_tmout`

Return value indicating that a programmed timeout expired before a character was read.

**Value:** `-2`

**Used by:** `readkey`

**Description:**

Returned by the `readkey` function when the programmed timeout expires before a character is received from an input device. When `read_tmout` is returned the value in the target variable is invalid.

**See Also:** `read_ok`, `eof`, `read_error`, `readkey`

### `retract_plane_group`

Modal group number for retract plane.

**See Also:** `G98`, `G99`

### `spindle_units_group`

Modal group number for spindle units (spindle 1).

**See Also:** `spindless_units_group`, `spindlesss_units_group`, `spindlessss_units_group`

### `spindless_units_group`

Modal group number for spindle units (spindle 2).

**See Also:** `spindle_units_group`, `spindlesss_units_group`, `spindlessss_units_group`

### `spindlesss_units_group`

Modal group number for spindle units (spindle 3).

**See Also:** `spindle_units_group`, `spindless_units_group`, `spindlessss_units_group`

### `spindlessss_units_group`

Modal group number for spindle units (spindle 4).

**See Also:** `spindle_units_group`, `spindless_units_group`, `spindlesss_units_group`

### `spline_group`

Modal group number for spline mode.

**See Also:** `splineon`, `splineoff`

### `uniform`

Spline type: uniform.

**Used by:** `st`

**See Also:** `bspline`, `chord`, `splineon`, `st`

## Stream Constants

### `keyboard`

Stream constant for keyboard input.

**Used by:** `read`, `readkey`

**See Also:** `vdu`, `printer`

### `printer`

Stream constant for printer output.

**Used by:** `write`

**See Also:** `vdu`, `keyboard`

### `vdu`

Stream constant for VDU (screen) output.

**Used by:** `write`

**See Also:** `keyboard`, `printer`
