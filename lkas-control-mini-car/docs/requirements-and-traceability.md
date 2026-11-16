# Requirements and Verification Traceability

This is a working student-project specification, not an ISO 26262 safety case or certification claim.

| ID | Requirement / interface | Evidence or test | Status |
|---|---|---|---|
| REQ-01 | Preserve original artifacts unchanged and distinguish them from new work. | Original-material inventory and project README. | Original artifacts unavailable; reconstruction pending. |
| REQ-02 | State units, coordinates, assumptions, and operating conditions for every model input/output. | Reference parameter function and scenario description. | Documented for the new reference case; historical definitions unresolved. |
| REQ-03 | Run the reference controller/vehicle model without Simulink or add-on Toolbox dependencies. | `tests/test_lkas_reference.m` in MATLAB R2016a. | Seven scenario checks passed. |
| REQ-04 | Constrain the reference front-wheel steering command to the configured saturation. | Automated output-bound assertion in each scenario. | Passed for all seven scenarios. |
| REQ-05 | Keep measured results distinct from historical presentation results and hardware claims. | Separate reference CSV/PNG and evidence labels. | Implemented; simulation outputs archived, no hardware result. |
| REQ-06 | Separate historical mini-car evidence from the new MATLAB simulation and mark missing evidence as unverified. | `original/mini-car/README.md` and portfolio README. | Evidence location prepared; photos/source materials not provided. |

## Current reference interface

| Signal | Unit | Definition |
|---|---|---|
| Lateral error `e_y` | m | Vehicle lateral position relative to the active path reference; positive is left. |
| Heading error `e_psi` | rad | Vehicle heading minus reference heading; positive is counter-clockwise/left. |
| Steering command `delta` | rad | Front road-wheel angle; positive steers left. |
| Yaw rate `r` | rad/s | Vehicle yaw rate, positive counter-clockwise. |
| Reference curvature | 1/m | Zero for straight road; 0.003 1/m for the constant-curve case; time-varying for the lane-change reference. |

The linear bicycle model assumes small slip angles, positive longitudinal speed (sampled and held within each control period), linear tire cornering forces, and no tire saturation, actuator dynamics, road bank, or measurement delay. The sign convention and candidate axle stiffness interpretation must be checked against original artifacts before treating the model as a reconstruction.

## Verification records

MATLAB R2016a scenario suite and automatic checks were executed on 2026-11-16. Saved CSV values are checked against recomputed scenario metrics and baseline time-series values; generated graph files are checked for presence. The resulting CSV/PNG files are in `results/simulation/`. No Simulink reproduction, mini-car measurement, or ISO verification result exists.
