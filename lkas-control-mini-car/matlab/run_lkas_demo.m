function result = run_lkas_demo()
%RUN_LKAS_DEMO Run the reference simulation and save its measured outputs.

projectRoot = fileparts(fileparts(mfilename('fullpath')));
outputDirectory = fullfile(projectRoot, 'results', 'simulation');
if ~exist(outputDirectory, 'dir')
    mkdir(outputDirectory);
end

scenarios = lkas_scenarios();
result = lkas_reference_simulation(scenarios(3));
fprintf('Large-initial-offset reference case (not original-model reproduction)\n');
fprintf('RMS lateral error: %.6f m\n', result.rmsLateralError);
fprintf('Maximum absolute lateral error: %.6f m\n', result.maxAbsLateralError);
fprintf('Maximum absolute heading error: %.6f rad\n', result.maxAbsHeadingError);
fprintf('Maximum absolute yaw rate: %.6f rad/s\n', result.maxAbsYawRate);
fprintf('Maximum absolute steering: %.6f deg\n', result.maxAbsSteeringAngle * 180/pi);
fprintf('Steering saturation samples: %d\n', result.steeringSaturationCount);
fprintf('Final lateral error: %.6f m\n', result.finalLateralError);

logTable = table(result.time, result.lateralError, result.headingError, ...
    result.yawRate, result.steeringAngle, ...
    'VariableNames', {'time_s', 'lateral_error_m', 'heading_error_rad', ...
    'yaw_rate_rad_s', 'steering_angle_rad'});
csvPath = fullfile(outputDirectory, 'reference_simulation.csv');
if exist('writetable', 'file') == 2
    writetable(logTable, csvPath);
else
    error('LKAS:WritetableUnavailable', ...
        'This MATLAB installation does not provide writetable; CSV was not saved.');
end

figureHandle = figure('Visible', 'off', 'Color', 'w', ...
    'Position', [100, 100, 1000, 760]);
subplot(3, 1, 1);
plot(result.time, result.lateralError, 'LineWidth', 1.4);
grid on;
set(gca, 'FontSize', 10, 'LineWidth', 0.8);
ylabel('e_y (m)');
title('MATLAB Simulation: Large Initial Offset', 'FontSize', 12, ...
    'FontWeight', 'bold');
subplot(3, 1, 2);
plot(result.time, result.headingError * 180/pi, 'LineWidth', 1.4);
grid on;
set(gca, 'FontSize', 10, 'LineWidth', 0.8);
ylabel('e_\psi (deg)');
subplot(3, 1, 3);
plot(result.time, result.steeringAngle * 180/pi, 'LineWidth', 1.4);
grid on;
set(gca, 'FontSize', 10, 'LineWidth', 0.8);
ylim([-35, 35]);
ylabel('\delta (deg)');
xlabel('Time (s)');
pngPath = fullfile(outputDirectory, 'reference_simulation.png');
print(figureHandle, pngPath, '-dpng', '-r120');
close(figureHandle);
fprintf('CSV: %s\nPNG: %s\n', csvPath, pngPath);
end
