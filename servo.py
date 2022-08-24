from hashlib import new
import os
os.environ['GPIOZERO_PIN_FACTORY']='pigpio'
from gpiozero import Servo
import time
import math

from joysticks import get_controller
contr = get_controller()

servo = Servo(19, min_pulse_width=.5/1000, max_pulse_width=2.5/1000, frame_width=20/1000)
servo1 = Servo(12, min_pulse_width=.5/1000, max_pulse_width=2.5/1000, frame_width=20/1000)

servo.value = 0
servo1.value = 0
while True:                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  
    contr.run()
    #servo.value += contr[4] * 0.06535947712
    #servo1.value += contr[5] * 0.06535947712