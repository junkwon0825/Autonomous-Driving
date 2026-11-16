function result = lkas_reference_simulation(scenario)
%LKAS_REFERENCE_SIMULATION Simulate a candidate PID and bicycle vehicle model.
% This is a new educational reference model, not the unavailable original.

p = lkas_reference_parameters();
if nargin < 1 || isempty(scenario)
    scenarios = lkas_scenarios();
    scenario = scenarios(1);
end

sampleCount = round(scenario.duration / p.sampleTime) + 1;
time = (0:sampleCount-1)' * p.sampleTime;
state = [0; 0; scenario.initialLateralError; scenario.initialHeadingError];

lateralIntegral = 0;
headingIntegral = 0;
previousLateralMeasurement = state(3) + sensor_noise(0, scenario.sensorNoise);
previousHeadingMeasurement = state(4) + sensor_noise(0, scenario.headingNoise);

result.name = scenario.name;
result.time = time;
result.lateralError = zeros(sampleCount, 1);
result.headingError = zeros(sampleCount, 1);
result.yawRate = zeros(sampleCount, 1);
result.steeringAngle = zeros(sampleCount, 1);
result.speed = zeros(sampleCount, 1);
result.referenceLateralOffset = zeros(sampleCount, 1);
result.turnSignal = false(sampleCount, 1);
result.mode = cell(sampleCount, 1);
result.parameters = p;
result.scenario = scenario;

for k = 1:sampleCount
    t = time(k);
    speed = scenario_speed(t, scenario);
    [referenceOffset, curvature] = reference_path(t, speed, scenario);
    lateralError = state(3);
    headingError = state(4);
    lateralMeasurement = lateralError + sensor_noise(t, scenario.sensorNoise);
    headingMeasurement = headingError + sensor_noise(t, scenario.headingNoise);
    lateralDerivative = (lateralMeasurement - previousLateralMeasurement) / p.sampleTime;
    headingDerivative = (headingMeasurement - previousHeadingMeasurement) / p.sampleTime;
    candidateLateralIntegral = lateralIntegral + lateralMeasurement * p.sampleTime;
    candidateHeadingIntegral = headingIntegral + headingMeasurement * p.sampleTime;

    rawSteering = steering_command(lateralMeasurement, headingMeasurement, ...
        candidateLateralIntegral, candidateHeadingIntegral, ...
        lateralDerivative, headingDerivative, p);
    integralSteeringChange = -(p.lateralPID(2) * lateralMeasurement ...
        + p.headingPID(2) * headingMeasurement) * p.sampleTime;
    drivesFurtherIntoSaturation = ...
        (rawSteering > p.maxSteeringAngle && integralSteeringChange > 0) ...
        || (rawSteering < -p.maxSteeringAngle && integralSteeringChange < 0);
    if ~drivesFurtherIntoSaturation
        lateralIntegral = candidateLateralIntegral;
        headingIntegral = candidateHeadingIntegral;
    else
        rawSteering = steering_command(lateralMeasurement, headingMeasurement, ...
            lateralIntegral, headingIntegral, lateralDerivative, headingDerivative, p);
    end
    steering = min(max(rawSteering, -p.maxSteeringAngle), p.maxSteeringAngle);

    result.lateralError(k) = lateralError;
    result.headingError(k) = headingError;
    result.yawRate(k) = state(2);
    result.steeringAngle(k) = steering;
    result.speed(k) = speed;
    result.referenceLateralOffset(k) = referenceOffset;
    result.turnSignal(k) = scenario.laneChange ...
        && t >= scenario.laneChangeStart - 1 ...
        && t < scenario.laneChangeEnd;
    result.mode{k} = control_mode(t, scenario);

    previousLateralMeasurement = lateralMeasurement;
    previousHeadingMeasurement = headingMeasurement;
    if k < sampleCount
        state = integrate_vehicle(state, steering, speed, curvature, ...
            t, scenario, p);
    end
end

result.rmsLateralError = sqrt(mean(result.lateralError.^2));
result.maxAbsLateralError = max(abs(result.lateralError));
result.maxAbsHeadingError = max(abs(result.headingError));
result.maxAbsYawRate = max(abs(result.yawRate));
result.maxAbsSteeringAngle = max(abs(result.steeringAngle));
result.steeringSaturationCount = sum(abs(result.steeringAngle) ...
    >= p.maxSteeringAngle - 1e-12);
result.finalLateralError = result.lateralError(end);
result.finalHeadingError = result.headingError(end);
if scenario.laneChange
    result.settlingTime = NaN;
else
    result.settlingTime = settling_time(time, result.lateralError, 0.02);
end
result.lateralOvershoot = lateral_overshoot( ...
    scenario.initialLateralError, result.lateralError);
end

function output = steering_command(lateralError, headingError, ...
        lateralIntegral, headingIntegral, lateralDerivative, headingDerivative, p)
lateralOutput = p.lateralPID(1) * lateralError ...
    + p.lateralPID(2) * lateralIntegral ...
    + p.lateralPID(3) * lateralDerivative;
headingOutput = p.headingPID(1) * headingError ...
    + p.headingPID(2) * headingIntegral ...
    + p.headingPID(3) * headingDerivative;
output = -lateralOutput - headingOutput;
end

function value = sensor_noise(time, amplitude)
value = amplitude * (sin(2*pi*1.7*time) + 0.4*sin(2*pi*3.1*time)) / 1.4;
end

function speed = scenario_speed(time, scenario)
if scenario.duration <= 0
    error('LKAS:InvalidDuration', 'Scenario duration must be positive.');
end
fraction = min(max(time / scenario.duration, 0), 1);
speed = scenario.speedStart + fraction * (scenario.speedEnd - scenario.speedStart);
end

function [offset, curvature] = reference_path(time, speed, scenario)
offset = 0;
curvature = scenario.curvature;
if ~scenario.laneChange
    return;
end

transitionDuration = scenario.laneChangeEnd - scenario.laneChangeStart;
if transitionDuration <= 0
    error('LKAS:InvalidLaneChange', 'Lane-change end must follow its start.');
end
progress = min(max((time - scenario.laneChangeStart) / transitionDuration, 0), 1);
offset = scenario.laneWidth * (10*progress^3 - 15*progress^4 + 6*progress^5);
offsetRate = scenario.laneWidth / transitionDuration ...
    * (30*progress^2 - 60*progress^3 + 30*progress^4);
offsetAcceleration = scenario.laneWidth / transitionDuration^2 ...
    * (60*progress - 180*progress^2 + 120*progress^3);
speedRate = (scenario.speedEnd - scenario.speedStart) / scenario.duration;
heading = atan2(offsetRate, speed);
headingRate = (offsetAcceleration * speed - offsetRate * speedRate) ...
    / (speed^2 + offsetRate^2);
curvature = headingRate / sqrt(speed^2 + offsetRate^2);
end

function mode = control_mode(time, scenario)
if ~scenario.laneChange
    mode = 'LANE_KEEPING';
elseif time < scenario.laneChangeStart - 1
    mode = 'LANE_KEEPING';
elseif time < scenario.laneChangeStart
    mode = 'TURN_SIGNAL_ACTIVE';
elseif time < scenario.laneChangeEnd
    mode = 'LANE_CHANGE';
else
    mode = 'LANE_KEEPING_RESUME';
end
end

function value = lateral_overshoot(initialError, lateralError)
if abs(initialError) < 1e-9
    value = NaN;
else
    value = max(0, -min(sign(initialError) * lateralError));
end
end

function value = settling_time(time, errorSignal, tolerance)
value = NaN;
for k = 1:numel(time)
    if all(abs(errorSignal(k:end)) <= tolerance)
        value = time(k);
        return;
    end
end
end

function nextState = integrate_vehicle(state, steering, speed, curvature, ...
        time, scenario, p)
steps = round(p.sampleTime / p.integrationStep);
stepSize = p.sampleTime / steps;
nextState = state;
for n = 1:steps
    substepTime = time + (n-1) * stepSize;
    k1 = vehicle_derivative(nextState, steering, speed, curvature, ...
        substepTime, scenario, p);
    k2 = vehicle_derivative(nextState + 0.5 * stepSize * k1, steering, ...
        speed, curvature, substepTime + 0.5*stepSize, scenario, p);
    k3 = vehicle_derivative(nextState + 0.5 * stepSize * k2, steering, ...
        speed, curvature, substepTime + 0.5*stepSize, scenario, p);
    k4 = vehicle_derivative(nextState + stepSize * k3, steering, ...
        speed, curvature, substepTime + stepSize, scenario, p);
    nextState = nextState + (stepSize / 6) * (k1 + 2*k2 + 2*k3 + k4);
end
end

function derivative = vehicle_derivative(state, steering, speed, curvature, ...
        time, scenario, p)
lateralVelocity = state(1);
yawRate = state(2);
headingError = state(4);

frontSlip = steering - (lateralVelocity + p.frontAxleDistance * yawRate) / speed;
rearSlip = -(lateralVelocity - p.rearAxleDistance * yawRate) / speed;
frontForce = p.frontCorneringStiffness * frontSlip;
rearForce = p.rearCorneringStiffness * rearSlip;
lateralForceDisturbance = scenario.lateralDisturbance ...
    * sin(2*pi*0.8*time);

lateralAcceleration = (frontForce + rearForce + lateralForceDisturbance) ...
    / p.mass - speed * yawRate;
yawAcceleration = (p.frontAxleDistance * frontForce ...
    - p.rearAxleDistance * rearForce) / p.yawInertia;
lateralErrorRate = lateralVelocity + speed * headingError;
headingErrorRate = yawRate - speed * curvature;

derivative = [lateralAcceleration; yawAcceleration; ...
    lateralErrorRate; headingErrorRate];
end
