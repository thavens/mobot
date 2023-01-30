from imu import IMUPoint, IMU
import numpy as np

imu = IMU(500, 16, use_calibration=False)
n = 10000
data = np.zeros((n, 7))
for i in range(n):
    data[i, :] = imu.imudata()[:]
covariance = np.cov(data)
mean = np.mean(data, axis=0)

with open('calibration.txt', 'w') as f:
    f.write(','.join(IMUPoint._fields))
    f.write('\n')
    f.write(','.join([str(i) for i in mean]))
    f.write('\n')
    for i in covariance:
        f.write(','.join(str(j) for j in i))
        f.write('\n')


