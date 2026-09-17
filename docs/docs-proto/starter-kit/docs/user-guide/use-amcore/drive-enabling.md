# Drive enabling

AMCore provides **core logic** to manage drive enabling, so you may not need to handle these details manually. However, if you are not using our provided core logic, this section explains how to control and monitor the drive state.

AMCore simplifies the DS402 state machine - which in its full implementation contains 8 states, 17 transitions, and 7 commands - by abstracting much of the complexity. The variables `G_DD_COE_DRIVE_STATE_COMMANDEDx` and `G_DD_COE_DRIVE_STATE_ACTUALx` reflect the DS402 standard, while the other shared memory variables offer a more straightforward interface.

In a typical scenario, you only need to set `G_DD_DRIVE_STATE_COMMANDx` to the desired state and verify the result in `G_DD_DRIVE_STATE_ACTUALx`. All other variables, such as `G_DD_DRIVE_STATE_PERIODx` and `G_DD_COE_DRIVE_STATE_ACTUALx`, are primarily for diagnostics and troubleshooting.

## Drive State Variables

| Category            | Description                                                       | Variable                    |
| ------------------- | ----------------------------------------------------------------- | --------------------------- |
| Command Drive State | Controls the drive's operational state.                           | `G_DD_DRIVE_STATE_COMMANDx` |
| Actual Drive State  | Shows the current state, based on the simplified CoE/DS402 model. | `G_DD_DRIVE_STATE_ACTUALx`  |



> [!NOTE]
> See [Variable Reference](../reference/variable-reference.md#variable-reference) for more information

### Command and Actual Drive State Behaviour

* **State Transition Process:**
When a change occurs in `G_DD_COMMAND_DRIVE_STATE`, AMCore transitions through the necessary CoE drive states to reach the requested state. You can monitor this progress via `G_DD_ACTUAL_DRIVE_STATE`.

* **Drive Command Examples:**

  * `G_DD_COMMAND_DRIVE_STATE::POWER_ON` attempts to bring the drive to the CoE Switched On state (**POWERED_ON**).
  * `G_DD_COMMAND_DRIVE_STATE::POWER_TORQUE_ON` attempts to bring the drive to the CoE Operation Enabled state (**POWERED_TORQUED_ON**).

* **Drive State Feedback:**

  * `G_DD_ACTUAL_DRIVE_STATE::POWERED_ON` indicates that the drive is in the CoE Switched On state.
  * `G_DD_ACTUAL_DRIVE_STATE::POWERED_TORQUED_ON` indicates that the drive is in the CoE Operation Enabled state (e.g., Quick Stop Active, Fault Reaction Active).
  * Additionally, `G_DD_READY_TO_OPERATEx` signifies that the drive is fully prepared for operation.

## Diagnostics

Use these diagnostic variables to verify state transitions and troubleshoot any unexpected behavior.

| Diagnostic Variable               | Description                                                              |
| --------------------------------- | ------------------------------------------------------------------------ |
| `G_DD_COE_DRIVE_STATE_COMMANDEDx` | Reflects the drive state command as defined by the DS402 standard (CoE). |
| `G_DD_COE_DRIVE_STATE_ACTUALx`    | Reflects the actual drive state based on the DS402 standard (CoE).       |
| `G_DD_DRIVE_STATE_PERIODx`        | Tracks how long the drive remains in a state, aiding in troubleshooting. |