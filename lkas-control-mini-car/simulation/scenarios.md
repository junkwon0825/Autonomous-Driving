# Simulation Scenarios

## Implemented reference case

`matlab/lkas_reference_simulation.m` currently contains one deterministic case:

- Straight reference path, curvature `0 1/m`
- Constant speed `10 m/s`
- Initial lateral error `+0.15 m`
- Initial heading error `+0.05 rad`
- Controller sample time `0.1 s`
- Linear dynamic bicycle model with a `0.001 s` RK4 integration step
- Recorded PID gains and a provisional `±30°` front-wheel steering saturation

These are explicit reference-simulation choices, not verified historical test conditions. The recorded `Error gain = 6000` is intentionally excluded because its location and units are unknown.

## Not yet implemented

Curved/S-shaped path, speed variation, turn-signal state behavior, disturbance/noise, sensor delay, and PID gain sweeps require original scenario details or a separately reviewed extension. Do not report them as completed experiments.
