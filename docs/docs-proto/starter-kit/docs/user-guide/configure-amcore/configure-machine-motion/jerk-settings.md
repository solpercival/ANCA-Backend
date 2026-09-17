# Jerk settings

## Transition jerk limit

When going from one move to the next, if the two moves are not completely tangent or do not have the same curvature at the transition point, a momentary jerk spike will be generated. This jerk spike is called transition jerk. AMCore limits the transition jerk by lowering the feedrate at the transition if required.

As an example, if you run the below part program and plot G\_SERVO\_CP1, then take derivatives from it 3 times, you can see a jerk spike at the transition from line N30 to line N40.

```
N10 G0X0Y0
N20 F60000
N30 G1X10Y1
N40 G1X20Y0
```