# Requirements and Verification Traceability

This is a working student-project specification, not an ISO 26262 safety case or certification claim.

| ID | Requirement / interface | Evidence or test | Status |
|---|---|---|---|
| REQ-01 | Preserve original artifacts unchanged and distinguish them from new work. | Original-material inventory and project README. | Original artifacts unavailable; reconstruction pending. |
| REQ-02 | State units, coordinates, assumptions, and operating conditions for every model input/output. | Reference parameter function and scenario description. | Documented for the new reference case; historical definitions unresolved. |
| REQ-03 | Run the reference controller/vehicle model without Simulink or add-on Toolbox dependencies. | `tests/test_lkas_reference.m` in base MATLAB. | Pending MATLAB execution. |
| REQ-04 | Constrain the reference front-wheel steering command to the configured saturation. | Automated output-bound assertion. | Pending MATLAB execution. |
| REQ-05 | Keep measured results distinct from historical presentation results and hardware claims. | Separate reference CSV/PNG and evidence labels. | Implemented in documentation; no measured artifact yet. |
| REQ-06 | Stop safely on perception failure, communication timeout, or emergency stop in the future mini car. | Hardware-in-loop and controlled-track safety tests. | Not implemented; hardware and interface are not selected. |

## Current reference interface

| Signal | Unit | Definition |
|---|---|---|
| Lateral error `e_y` | m | Vehicle lateral position minus straight reference position; positive is left. |
| Heading error `e_psi` | rad | Vehicle heading minus reference heading; positive is counter-clockwise/left. |
| Steering command `delta` | rad | Front road-wheel angle; positive steers left. |
| Yaw rate `r` | rad/s | Vehicle yaw rate, positive counter-clockwise. |
| Reference curvature | 1/m | Constant zero for the implemented straight-road case. |

The linear bicycle model assumes small slip angles, constant positive longitudinal speed, linear tire cornering forces, and no tire saturation, actuator dynamics, road bank, or measurement delay. The sign convention and candidate axle stiffness interpretation must be checked against original artifacts before treating the model as a reconstruction.

## Verification records

No MATLAB run log, Simulink result, mini-car measurement, or ISO verification result is included until it has actually been produced and reviewed.
