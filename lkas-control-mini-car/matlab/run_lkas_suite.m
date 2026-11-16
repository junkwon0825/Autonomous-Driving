function summary = run_lkas_suite()
%RUN_LKAS_SUITE Execute all deterministic reference scenarios and save evidence.

projectRoot = fileparts(fileparts(mfilename('fullpath')));
outputDirectory = fullfile(projectRoot, 'results', 'simulation');
if ~exist(outputDirectory, 'dir')
    mkdir(outputDirectory);
end
scenarios = lkas_scenarios();
results = cell(numel(scenarios), 1);

names = cell(numel(scenarios), 1);
rmsError = zeros(numel(scenarios), 1);
maxError = zeros(numel(scenarios), 1);
maxHeading = zeros(numel(scenarios), 1);
maxYawRate = zeros(numel(scenarios), 1);
maxSteering = zeros(numel(scenarios), 1);
saturationCount = zeros(numel(scenarios), 1);
settlingTime = NaN(numel(scenarios), 1);
lateralOvershoot = NaN(numel(scenarios), 1);
finalLateralError = zeros(numel(scenarios), 1);

allScenarioNames = cell(0, 1);
allTime = zeros(0, 1);
allLateralError = zeros(0, 1);
allHeadingError = zeros(0, 1);
allYawRate = zeros(0, 1);
allSteering = zeros(0, 1);
allSpeed = zeros(0, 1);
allReferenceOffset = zeros(0, 1);
allTurnSignal = false(0, 1);
allMode = cell(0, 1);

for k = 1:numel(scenarios)
    result = lkas_reference_simulation(scenarios(k));
    results{k} = result;
    names{k} = result.name;
    rmsError(k) = result.rmsLateralError;
    maxError(k) = result.maxAbsLateralError;
    maxHeading(k) = result.maxAbsHeadingError;
    maxYawRate(k) = result.maxAbsYawRate;
    maxSteering(k) = result.maxAbsSteeringAngle * 180/pi;
    saturationCount(k) = result.steeringSaturationCount;
    settlingTime(k) = result.settlingTime;
    lateralOvershoot(k) = result.lateralOvershoot;
    finalLateralError(k) = result.finalLateralError;

    sampleCount = numel(result.time);
    allScenarioNames = [allScenarioNames; repmat({result.name}, sampleCount, 1)];
    allTime = [allTime; result.time];
    allLateralError = [allLateralError; result.lateralError];
    allHeadingError = [allHeadingError; result.headingError];
    allYawRate = [allYawRate; result.yawRate];
    allSteering = [allSteering; result.steeringAngle];
    allSpeed = [allSpeed; result.speed];
    allReferenceOffset = [allReferenceOffset; result.referenceLateralOffset];
    allTurnSignal = [allTurnSignal; result.turnSignal];
    allMode = [allMode; result.mode];
end

summary = table(names, rmsError, maxError, maxHeading, maxYawRate, ...
    maxSteering, saturationCount, settlingTime, lateralOvershoot, ...
    finalLateralError, ...
    'VariableNames', {'scenario', 'rms_lateral_error_m', ...
    'max_abs_lateral_error_m', 'max_abs_heading_error_rad', ...
    'max_abs_yaw_rate_rad_s', 'max_abs_steering_deg', ...
    'steering_saturation_samples', 'settling_time_s', ...
    'lateral_overshoot_m', 'final_lateral_error_m'});
summaryPath = fullfile(outputDirectory, 'scenario_metrics.csv');
writetable(summary, summaryPath);

timeSeries = table(allScenarioNames, allTime, allLateralError, ...
    allHeadingError, allYawRate, allSteering, allSpeed, ...
    allReferenceOffset, allTurnSignal, allMode, ...
    'VariableNames', {'scenario', 'time_s', 'lateral_error_m', ...
    'heading_error_rad', 'yaw_rate_rad_s', 'steering_angle_rad', ...
    'speed_m_s', 'reference_lateral_offset_m', 'turn_signal', 'mode'});
timeSeriesPath = fullfile(outputDirectory, 'scenario_timeseries.csv');
writetable(timeSeries, timeSeriesPath);

figureHandle = figure('Visible', 'off');
plotScenarios(results, 'lateralError', 1, 'Lateral error (m)');
plotScenarios(results, 'headingError', 2, 'Heading error (deg)', 180/pi);
plotScenarios(results, 'steeringAngle', 3, 'Steering command (deg)', 180/pi);
plotScenarios(results, 'speed', 4, 'Longitudinal speed (m/s)');
pngPath = fullfile(outputDirectory, 'scenario_comparison.png');
print(figureHandle, pngPath, '-dpng', '-r130');
close(figureHandle);

fprintf('Ran %d deterministic reference scenarios.\n', numel(results));
disp(summary);
fprintf('Metrics: %s\nTime series: %s\nPlots: %s\n', ...
    summaryPath, timeSeriesPath, pngPath);
end

function plotScenarios(results, fieldName, position, plotTitle, scale)
if nargin < 5
    scale = 1;
end
subplot(2, 2, position);
hold on;
lineHandles = zeros(numel(results), 1);
for k = 1:numel(results)
    result = results{k};
    lineHandles(k) = plot(result.time, result.(fieldName) * scale);
end
grid on;
xlabel('Time (s)');
ylabel(plotTitle);
title(plotTitle);
if position == 1
    names = cell(numel(results), 1);
    for k = 1:numel(results)
        names{k} = results{k}.name;
    end
    legend(lineHandles, names, 'Interpreter', 'none', 'Location', 'best');
end
hold off;
end
