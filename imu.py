import smbus
import time
from collections import namedtuple
from pathlib import Path

DEVICE_BUS = 1
DEVICE_ADDR = 0x68

# device registers
reg = {"SELF_TEST_X": 0x0D,
    "SELF_TEST_Y": 0x0E,
    "SELF_TEST_Z": 0x0F,
    "SELF_TEST_A": 0x10,
    "SMPLRT_DIV": 0x19,
    "CONFIG": 0x1A,
    "GYRO_CONFIG": 0x1B,
    "ACCEL_CONFIG": 0x1C,
    "FIFO_EN": 0x23,
    "I2C_MST_CTRL": 0x24,
    "I2C_SLV0_ADDR": 0x25,
    "I2C_SLV0_REG": 0x26,
    "I2C_SLV0_CTRL": 0x27,
    "I2C_SLV1_ADDR": 0x28,
    "I2C_SLV1_REG": 0x29,
    "I2C_SLV1_CTRL": 0x2A,
    "I2C_SLV2_ADDR": 0x2B,
    "I2C_SLV2_REG": 0x2C,
    "I2C_SLV2_CTRL": 0x2D,
    "I2C_SLV3_ADDR": 0x2E,
    "I2C_SLV3_REG": 0x2F,
    "I2C_SLV3_CTRL": 0x30,
    "I2C_SLV4_ADDR": 0x31,
    "I2C_SLV4_REG": 0x32,
    "I2C_SLV4_DO": 0x33,
    "I2C_SLV4_CTRL": 0x34,
    "I2C_SLV4_DI": 0x35,
    "I2C_MST_STATUS": 0x36,
    "INT_PIN_CFG": 0x37,
    "INT_ENABLE": 0x38,
    "INT_STATUS": 0x3A,
    "ACCEL_XOUT_H": 0x3B,
    "ACCEL_XOUT_L": 0x3C,
    "ACCEL_YOUT_H": 0x3D,
    "ACCEL_YOUT_L": 0x3E,
    "ACCEL_ZOUT_H": 0x3F,
    "ACCEL_ZOUT_L": 0x40,
    "TEMP_OUT_H": 0x41,
    "TEMP_OUT_L": 0x42,
    "GYRO_XOUT_H": 0x43,
    "GYRO_XOUT_L": 0x44,
    "GYRO_YOUT_H": 0x45,
    "GYRO_YOUT_L": 0x46,
    "GYRO_ZOUT_H": 0x47,
    "GYRO_ZOUT_L": 0x48,
    "EXT_SENS_DATA_00": 0x49,
    "EXT_SENS_DATA_01": 0x4A,
    "EXT_SENS_DATA_02": 0x4B,
    "EXT_SENS_DATA_03": 0x4C,
    "EXT_SENS_DATA_04": 0x4D,
    "EXT_SENS_DATA_05": 0x4E,
    "EXT_SENS_DATA_06": 0x4F,
    "EXT_SENS_DATA_07": 0x50,
    "EXT_SENS_DATA_08": 0x51,
    "EXT_SENS_DATA_09": 0x52,
    "EXT_SENS_DATA_10": 0x53,
    "EXT_SENS_DATA_11": 0x54,
    "EXT_SENS_DATA_12": 0x55,
    "EXT_SENS_DATA_13": 0x56,
    "EXT_SENS_DATA_14": 0x57,
    "EXT_SENS_DATA_15": 0x58,
    "EXT_SENS_DATA_16": 0x59,
    "EXT_SENS_DATA_17": 0x5A,
    "EXT_SENS_DATA_18": 0x5B,
    "EXT_SENS_DATA_19": 0x5C,
    "EXT_SENS_DATA_20": 0x5D,
    "EXT_SENS_DATA_21": 0x5E,
    "EXT_SENS_DATA_22": 0x5F,
    "EXT_SENS_DATA_23": 0x60,
    "I2C_SLV0_DO": 0x63,
    "I2C_SLV1_DO": 0x64,
    "I2C_SLV2_DO": 0x65,
    "I2C_SLV3_DO": 0x66,
    "I2C_MST_DELAY_CT": 0x67,
    "SIGNAL_PATH_RES": 0x68,
    "USER_CTRL": 0x6A,
    "PWR_MGMT_1": 0x6B,
    "PWR_MGMT_2": 0x6C,
    "FIFO_COUNTH": 0x72,
    "FIFO_COUNTL": 0x73,
    "FIFO_R_W": 0x74,
    "WHO_AM_I": 0x75
}

# device register values
SELF_TEST = 0b11100000
FS_SEL = {
    250:    0b00000000,
    500:    0b00001000,
    1000:   0b00010000,
    2000:   0b00011000
}
AFS_SEL = {
    2:  0b00000000,
    4:  0b00001000,
    8:  0b00010000,
    16: 0b00011000
}

LSB_SENS = {
    2:  16384,
    4:  8192,
    8:  4096,
    16: 2048,
    250:  16384,
    500:  8192,
    1000:  4096,
    2000: 2048
}

clk_sel = 0b00000101
reset = 0b10000000
sleep = 0b01000000

IMUPoint = namedtuple("IMUPoint", ["ax", "ay", "az", "T", "roll", "pitch", "yaw"])
def tostr(self):
        return "IMU " + ", ".join([f'{name}={val:6.2f}'for name, val in zip(self._fields, self)])

def add(self, rhs):
    return IMUPoint(*[i + j for i, j in zip(self, rhs)])

def sub(self, rhs):
    return IMUPoint(*[i - j for i, j in zip(self, rhs)])

def iadd(self, rhs):
    IMUPoint[:] = [i + j for i, j in zip(self, rhs)]
    
def isub(self, rhs):
    IMUPoint[:] = [i - j for i, j in zip(self, rhs)]

IMUPoint.__str__ = tostr
IMUPoint.__add__ = add
IMUPoint.__iadd__ = iadd
IMUPoint.__isub__ = isub

def temp_deg (reg) :
    return reg / 340 + 36.53

class IMU:    
    """Generates IMU object.

        Args:
            gyro_sens (int): Gyroscope sensitivity [250, 500, 1000, 2000]
            accel_sens (int): Accelerometer sensitivity [2, 4, 8, 16]
            use_calibration (bool, optional): Use calibration file; only false for generating calibration file. Defaults to True.
    """
    
    def __self__(self, gyro_sens: int, accel_sens: int, use_calibration: bool=True):
        self.bus = smbus.SMBus(DEVICE_BUS)
        self.bus.write_byte_data(DEVICE_ADDR, reg["PWR_MGMT_1"], clk_sel)
        self.bus.write_byte_data(DEVICE_ADDR, reg["GYRO_CONFIG"], FS_SEL[gyro_sens])
        self.bus.write_byte_data(DEVICE_ADDR, reg["ACCEL_CONFIG"], AFS_SEL[accel_sens])
        self._fs_sel = LSB_SENS[gyro_sens]
        self._afs_sel = LSB_SENS[accel_sens]
        
        path = Path('calibration.txt')
        self.calib = None
        self.stats = None
        if path.exists():
            with open(path, 'r') as f:
                lines = f.readlines()
                if len(lines) > 1:
                    self.calib = IMUPoint(*[float(i) for i in lines[1].split(',')])
        
    def imudata(self):
        data = self.bus.read_i2c_block_data(DEVICE_ADDR, reg["ACCEL_XOUT_H"], 14)
        data = [int.from_bytes(data[i:i+2], 'big', signed=True) for i in range(0, len(data), 2)]
        data[0:3] = [i / self._afs_sel for i in data[0:3]]
        data[3] = temp_deg(data[3])
        data[4:8] = [i / self._fs_sel for i in data[4:8]]
        data = IMUPoint(*data)
        if self.calib:
            data -= self.calib
        return data

if __name__ == "__main__":
    imu = IMU(250, 2)
    n = 10000
    accum = IMUPoint(*[0] * 7)
    for i in range(n):
        accum += imu.imudata()
    mean = IMUPoint(*[i / n for i in accum])
    print(mean)
    
    