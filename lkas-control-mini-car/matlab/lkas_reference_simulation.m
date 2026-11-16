function result = lkas_reference_simulation()
%LKAS_REFERENCE_SIMULATION Independent PID + linear dynamic bicycle example.
% This is not a reconstruction of the unavailable original project.

p = lkas_reference_parameters();
sampleCount = round(p.duration / p.sampleTime) + 1;
time = (0:sampleCount-1)' * p.sampleTime;
state = [0; 0; p.initialLateralError; p.initialHeadingError];

lateralIntegral = 0;
headingIntegral = 0;
previousLateralError = state(3);
previousHeadingError = state(4);
result.time = time;
result.lateralError = zeros(sampleCount, 1);
result.headingError = zeros(sampleCount, 1);
result.yawRate = zeros(sampleCount, 1);
result.steeringAngle = zeros(sampleCount, 1);
result.parameters = p;

for k = 1:sampleCount
    lateralError = state(3);
    headingError = state(4);
    lateralDerivative = (lateralError - previousLateralError) / p.sampleTime;
    headingDerivative = (headingError - previousHeadingError) / p.sampleTime;
    candidateLateralIntegral = lateralIntegral + lateralError * p.sampleTime;
    candidateHeadingIntegral = headingIntegral + headingError * p.sampleTime;

    rawSteering = -pid_output(p.lateralPID, lateralError, ...
        candidateLateralIntegral, lateralDerivative) ...
        -pid_output(p.headingPID, headingError, ...
        candidateHeadingIntegral, headingDerivative);
    steering = min(max(rawSteering, -p.maxSteeringAngle), p.maxSteeringAngle);

    % Conditional integration prevents the integral term pushing farther into saturation.
    integralSteeringChange = -(p.lateralPID(2) * lateralError ...
        + p.headingPID(2) * headingError) * p.sampleTime;
    drivesFurtherIntoSaturation = ...
        (rawSteering > p.maxSteeringAngle && integralSteeringChange > 0) ...
        || (rawSteering < -p.maxSteeringAngle && integralSteeringChange < 0);
    if ~drivesFurtherIntoSaturation
        lateralIntegral = candidateLateralIntegral;
        headingIntegral = candidateHeadingIntegral;
    else
        rawSteering = -pid_output(p.lateralPID, lateralError, ...
            lateralIntegral, lateralDerivative) ...
            -pid_output(p.headingPID, headingError, ...
            headingIntegral, headingDerivative);
        steering = min(max(rawSteering, -p.maxSteeringAngle), p.maxSteeringAngle);
    end

    result.lateralError(k) = lateralError;
    result.headingError(k) = headingError;
    result.yawRate(k) = state(2);
    result.steeringAngle(k) = steering;

    previousLateralError = lateralError;
    previousHeadingError = headingError;
    if k < sampleCount
        state = integrate_vehicle(state, steering, p);
    end
end

result.rmsLateralError = sqrt(mean(result.lateralError.^2));
result.maxAbsLateralError = max(abs(result.lateralError));
result.maxAbsHeadingError = max(abs(result.headingError));
result.maxAbsYawRate = max(abs(result.yawRate));
result.maxAbsSteeringAngle = max(abs(result.steeringAngle));
result.steeringSaturationCount = sum(abs(result.steeringAngle) >= p.maxSteeringAngle - 1e-12);
result.finalLateralError = result.lateralError(end);
result.finalHeadingError = result.headingError(end);
end

function output = pid_output(gains, errorValue, integral, derivative)
output = gains(1) * errorValue + gains(2) * integral + gains(3) * derivative;
end

function nextState = integrate_vehicle(state, steering, p)
steps = round(p.sampleTime / p.integrationStep);
stepSize = p.sampleTime / steps;
nextState = state;
for n = 1:steps
    k1 = vehicle_derivative(nextState, steering, p);
    k2 = vehicle_derivative(nextState + 0.5 * stepSize * k1, steering, p);
    k3 = vehicle_derivative(nextState + 0.5 * stepSize * k2, steering, p);
    k4 = vehicle_derivative(nextState + stepSize * k3, steering, p);
    nextState = nextState + (stepSize / 6) * (k1 + 2*k2 + 2*k3 + k4);
end
end

function derivative = vehicle_derivative(state, steering, p)
lateralVelocity = state(1);
yawRate = state(2);
headingError = state(4);

frontForce = p.frontCorneringStiffness * ...
    (steering - (lateralVelocity + p.frontAxleDistance * yawRate) / p.speed);
rearForce = p.rearCorneringStiffness * ...
    (-(lateralVelocity - p.rearAxleDistance * yawRate) / p.speed);

lateralAcceleration = (frontForce + rearForce) / p.mass - p.speed * yawRate;
yawAcceleration = (p.frontAxleDistance * frontForce ...
    - p.rearAxleDistance * rearForce) / p.yawInertia;
lateralErrorRate = lateralVelocity + p.speed * headingError;
headingErrorRate = yawRate - p.speed * p.roadCurvature;

derivative = [lateralAcceleration; yawAcceleration; ...
    lateralErrorRate; headingErrorRate];
end
