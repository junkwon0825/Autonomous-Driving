import numpy as np
import matplotlib.pyplot as plt


# 차량 초기 상태
x = 0.0
y = 0.0
yaw = 0.0

# 차량 설정
v = 5.0
L = 2.7

# 조향각
delta = np.deg2rad(10)

# simulation 설정
dt = 0.1
simulation_time = 10.0

x_history = []
y_history = []


for t in np.arange(0, simulation_time, dt):

    x = x + v * np.cos(yaw) * dt
    y = y + v * np.sin(yaw) * dt

    yaw = yaw + (v / L) * np.tan(delta) * dt

    x_history.append(x)
    y_history.append(y)


plt.plot(x_history, y_history)
plt.xlabel("X [m]")
plt.ylabel("Y [m]")
plt.axis("equal")
plt.grid()

plt.show()