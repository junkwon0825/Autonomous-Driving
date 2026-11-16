function p = lkas_reference_parameters()
%LKAS_REFERENCE_PARAMETERS Candidate values transcribed from LKAS_PROJECT.md.
% These are not verified against the missing original MATLAB/Simulink model.

p.mass = 2045;                    % kg
p.yawInertia = 5428;              % kg*m^2
p.frontAxleDistance = 1.488;      % m, CG to front axle
p.rearAxleDistance = 1.712;       % m, CG to rear axle
p.frontCorneringStiffness = 38925; % N/rad, axle-total interpretation assumed
p.rearCorneringStiffness = 38255;  % N/rad, axle-total interpretation assumed
p.sampleTime = 0.1;               % s, controller sample time assumed
p.maxSteeringAngle = 30*pi/180;   % rad, front road-wheel angle assumed

p.lateralPID = [4.0, 0.1, 0.2];   % [Kp, Ki, Kd], recorded values
p.headingPID = [3.0, 0.1, 0.3];   % [Kp, Ki, Kd], recorded values
p.recordedErrorGain = 6000;        % Recorded, application/units unknown; not applied.

% Scenario choices for this independent reference simulation, not historical facts.
p.speed = 10;                      % m/s, constant
p.duration = 10;                   % s
p.initialLateralError = 0.15;      % m, vehicle relative to straight reference
p.initialHeadingError = 0.05;      % rad, vehicle heading relative to reference
p.roadCurvature = 0;               % 1/m, straight reference
p.integrationStep = 0.001;         % s, internal RK4 step
end
