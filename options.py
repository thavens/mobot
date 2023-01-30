DIRECT_SOCKET = False # don't use the forwarding server?
VIDEO = False # Use webcam? Identical option in client.py
SPEEDRATIO = 0.25 #0.48 # cap max speed 0-1
JOY_DEADBAND = 30 / 1000 # joystick threshold for zero
CONTROL_HEADER = 'con:'.encode('ascii')
WHEEL_RADIUS = 6.5 # inches
ACCEL_MAX = 6 # m/s^2
ALPHA_MAX = 1 # rad/s
CONTROL_SEND_FREQ = 60
BOARD_WIDTH = 18 # in

import math
WHEEL_RADIUS = WHEEL_RADIUS * 0.0254 # meters

ACCEL_MAX = ACCEL_MAX / WHEEL_RADIUS # angular accel omega/s
ACCEL_MAX = ACCEL_MAX * 30 / math.pi # rpm / s

BOARD_WIDTH *= 2.54 / 100 # m

ALPHA_MAX = ALPHA_MAX * BOARD_WIDTH / WHEEL_RADIUS * 30 / math.pi