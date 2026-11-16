function scenarios = lkas_scenarios()
%LKAS_SCENARIOS Deterministic reference cases, not historical experiments.

base = struct( ...
    'name', '', ...
    'duration', 10, ...
    'initialLateralError', 0.15, ...
    'initialHeadingError', 0.05, ...
    'curvature', 0, ...
    'speedStart', 10, ...
    'speedEnd', 10, ...
    'sensorNoise', 0, ...
    'headingNoise', 0, ...
    'lateralDisturbance', 0, ...
    'laneChange', false, ...
    'laneChangeStart', 3, ...
    'laneChangeEnd', 7, ...
    'laneWidth', 3.5);

scenarios = repmat(base, 7, 1);
scenarios(1).name = 'straight_recovery';
scenarios(1).initialLateralError = 0.02;
scenarios(1).initialHeadingError = 0.01;
scenarios(2).name = 'constant_curve';
scenarios(2).curvature = 0.003;
scenarios(2).initialLateralError = 0.05;
scenarios(2).initialHeadingError = 0.02;
scenarios(3).name = 'initial_offset';
scenarios(4).name = 'speed_ramp';
scenarios(4).initialLateralError = 0.05;
scenarios(4).initialHeadingError = 0.02;
scenarios(4).speedStart = 7;
scenarios(4).speedEnd = 15;
scenarios(5).name = 'sensor_noise_and_disturbance';
scenarios(5).initialLateralError = 0.05;
scenarios(5).initialHeadingError = 0.02;
scenarios(5).sensorNoise = 0.01;
scenarios(5).headingNoise = 0.003;
scenarios(5).lateralDisturbance = 300;
scenarios(6).name = 'turn_signal_lane_change';
scenarios(6).initialLateralError = 0;
scenarios(6).initialHeadingError = 0;
scenarios(6).laneChange = true;
scenarios(7).name = 'sensor_noise_baseline';
scenarios(7).initialLateralError = 0.05;
scenarios(7).initialHeadingError = 0.02;
end
