% Basic assertions for the independent MATLAB reference simulation.
projectRoot = fileparts(fileparts(mfilename('fullpath')));
addpath(fullfile(projectRoot, 'matlab'));

result = lkas_reference_simulation();
assert(numel(result.time) > 1, 'Simulation must produce multiple samples.');
assert(all(isfinite(result.lateralError)), 'Lateral error must remain finite.');
assert(all(isfinite(result.headingError)), 'Heading error must remain finite.');
assert(all(isfinite(result.yawRate)), 'Yaw rate must remain finite.');
assert(all(isfinite(result.steeringAngle)), 'Steering command must remain finite.');
assert(result.maxAbsSteeringAngle <= result.parameters.maxSteeringAngle + 1e-12, ...
    'Steering command exceeded the configured limit.');
assert(result.rmsLateralError < abs(result.parameters.initialLateralError), ...
    'The reference controller did not reduce lateral error RMS.');
fprintf('LKAS reference simulation checks passed.\n');
