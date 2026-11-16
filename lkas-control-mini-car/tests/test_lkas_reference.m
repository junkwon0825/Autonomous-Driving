% Basic assertions for all deterministic reference simulation scenarios.
projectRoot = fileparts(fileparts(mfilename('fullpath')));
addpath(fullfile(projectRoot, 'matlab'));

scenarios = lkas_scenarios();
assert(numel(scenarios) == 7, 'The reference suite must contain seven scenarios.');
results = cell(numel(scenarios), 1);
for k = 1:numel(scenarios)
    result = lkas_reference_simulation(scenarios(k));
    results{k} = result;
    assert(numel(result.time) > 1, 'Simulation must produce multiple samples.');
    assert(all(isfinite(result.lateralError)), 'Lateral error must remain finite.');
    assert(all(isfinite(result.headingError)), 'Heading error must remain finite.');
    assert(all(isfinite(result.yawRate)), 'Yaw rate must remain finite.');
    assert(all(isfinite(result.steeringAngle)), 'Steering command must remain finite.');
    assert(result.maxAbsSteeringAngle <= result.parameters.maxSteeringAngle + 1e-12, ...
        'Steering command exceeded the configured limit.');
end

assert(results{1}.rmsLateralError < abs(scenarios(1).initialLateralError), ...
    'Straight-road recovery did not reduce lateral-error RMS.');
assert(results{2}.rmsLateralError < 0.02, ...
    'Constant-curvature tracking error exceeded the test threshold.');
assert(results{4}.speed(end) > results{4}.speed(1), ...
    'Speed-ramp scenario did not increase speed.');
assert(any(results{5}.steeringAngle ~= results{7}.steeringAngle), ...
    'Noise-free comparison scenario must not match the noisy control output.');
assert(any(strcmp(results{6}.mode, 'TURN_SIGNAL_ACTIVE')), ...
    'Lane-change scenario is missing turn-signal state.');
assert(any(strcmp(results{6}.mode, 'LANE_CHANGE')), ...
    'Lane-change state was not entered.');
assert(any(strcmp(results{6}.mode, 'LANE_KEEPING_RESUME')), ...
    'Lane keeping was not resumed after the lane change.');
assert(any(results{6}.turnSignal), 'Turn-signal output was never active.');
assert(abs(results{6}.referenceLateralOffset(end) ...
    - scenarios(6).laneWidth) < 1e-12, ...
    'Lane-change reference did not reach the adjacent lane.');
assert(isnan(results{6}.settlingTime), ...
    'Lane-change transition must not report recovery settling time.');

fprintf('All %d LKAS reference scenario checks passed.\n', numel(scenarios));
