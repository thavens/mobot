import socket
import time
import select
from dataclasses import dataclass
import serial
from threading import Thread
from functools import reduce
import ctypes as ct
import datetime
import sys
import logging
import os
from serial.serialutil import SerialException
import math

from video import video_send, audio_send
import options

VIDEO = options.VIDEO # Use webcam? Identical option in control.py
    
if VIDEO:
    try:
        os.popen('sudo pigpiod')
        os.environ['GPIOZERO_PIN_FACTORY']='pigpio'
    except:
        pass
    from gpiozero import Servo
import math

######### Logger Options ############
logging.basicConfig(filename='client_daemon_log.txt',
                    filemode='w',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s> %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.NOTSET)
logging.info('Starting up')
#####################################

############ Client Options #########
hole_time = 1 #seconds
keep_alive = "client keep alive"
msg_bytes = str.encode(keep_alive, 'ascii')
if host := os.getenv('FORWARDING_HOST'):
    host = socket.gethostbyname(host)
    serveraddy = (host, 25565)
elif host := os.getenv('FORWARDING_SERVER'):
    serveraddy = (os.getenv('FORWARDING_SERVER'), 25565)
elif options.DIRECT_SOCKET:
    serveraddy = ('127.0.0.1', 25565)
else:
    logging.getLogger('Options').critical('Missing FORWARDING_HOST, or FORWARDING_SERVER env variable or direct socket option')
    raise Exception('Missing FORWARDING_HOST, or FORWARDING_SERVER env variable or direct socket option')
buffSize = 1024
#####################################

######### Daemon Options ############
START_FRAME = 0xABCD
TIME_SEND = 0.05
log_interval = 10
#####################################


udp = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM, proto=socket.IPPROTO_UDP)
udp.bind(('0.0.0.0', 25566))
udp.setblocking(False)

now = time.time()
future = now

################################################### Daemon Setup ############################################
brecieve = ['cmd1', 'cmd2', 'speedR_meas', 'speedL_meas', 'batVoltage', 'boardTemp']


class Wheels(Thread):
    def __init__(self):
        super(Wheels, self).__init__()
        self._data_turn = 0
        self._data_speed = 0
        self.time_log = 0
        self.control_update_msg = str.encode('info update:', 'ascii')

        failed = 1
        while failed:
            try:
                self.tty = serial.Serial('/dev/ttyUSB0', baudrate=115200, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE)
                failed = 0
            except SerialException as e:
                print('serial connection retry in 5s')
                print(f'{e}')
                logging.getLogger('Wheels') \
                    .exception(f'serial connection retry in 5s\n{e}')
                time.sleep(5)

    def send(self):
        msg = START_FRAME.to_bytes(2, 'little') \
            + self.data_turn.to_bytes(2, 'little', signed=True) \
            + self.data_speed.to_bytes(2, 'little', signed=True) \
            + ct.c_uint16(START_FRAME ^ self.data_turn ^ self.data_speed).value.to_bytes(2, 'little')
        self.tty.write(msg)

    def receive(self):
        if self.tty.in_waiting:
            data = self.tty.read_all()
            if len(data) == 18:
                incoming = [int.from_bytes(data[0:2], 'little', signed=False),
                int.from_bytes(data[2:4], 'little', signed=True),
                int.from_bytes(data[4:6], 'little', signed=True),
                int.from_bytes(data[6:8], 'little', signed=True),
                int.from_bytes(data[8:10], 'little', signed=True),
                int.from_bytes(data[10:12], 'little', signed=True),
                int.from_bytes(data[12:14], 'little', signed=True),
                int.from_bytes(data[14:16], 'little', signed=False)]
                checksum = int.from_bytes(data[16:18], 'little', signed=False)
                if reduce(lambda x, y: x ^ y, incoming) & 0xFFFF == checksum:
                    self.propogate(data)
                    if incoming[5] == 30:
                        logging.getLogger('daemon').info('Low Battery Exit')
                        sys.exit()
                    if self.time_log < (now := time.time()):
                        self.time_log = now + log_interval
                        logging.getLogger('daemon').info(
                            ' '.join([i + ': ' + str(j) for i, j in zip(brecieve, incoming[1:])])
                        )

    def propogate(self, data):
        global udp
        global serveraddy
        udp.sendto(self.control_update_msg + data, serveraddy)

    def run(self):
        try:
            itime_send = 0
            while True:
                now = time.time()
                self.receive()

                if itime_send < now:
                    itime_send = now + TIME_SEND
                    self.send()
                time.sleep(0.0001)
        except:
            logging.getLogger('daemon').exception('Exit due to:')
            sys.exit()
        
    def full_stop(self):
        while not (math.isclose(self.data_speed, 0) and math.isclose(self.data_turn, 0)):
            if abs(self.data_speed) > 50 or abs(self.data_turn) > 50:
                self._data_turn -= math.copysign(50, self._data_turn)
                self._data_speed -= math.copysign(50, self._data_turn)
            else:
                self._data_speed = 0
                self._data_turn = 0
            time.sleep(0.1)
    
    @property
    def data_speed(self) -> int:
        return int(self._data_speed)

    @data_speed.setter
    def data_speed(self, speed):
        if abs(speed - self._data_speed) > options.ACCEL_MAX:
            self._data_speed += options.ACCEL_MAX
        else:
            self._data_speed = speed
    
    @property
    def data_turn(self) -> int:
        return int(self._data_turn)

    @data_turn.setter
    def data_turn(self, turn):
        if abs(turn - self._data_turn) > options.ACCEL_MAX:
            self._data_turn += options.ACCEL_MAX
        else:
            self._data_turn = turn

wheels = Wheels()
wheels.start()

if VIDEO:
    # Servo stuff
    syaw = Servo(19, min_pulse_width=.5/1000, max_pulse_width=2.5/1000, frame_width=20/1000)
    spitch = Servo(12, min_pulse_width=.5/1000, max_pulse_width=2.5/1000, frame_width=20/1000)

    syaw.value = 0
    spitch.value = 0

    vsend = video_send()
    asend = audio_send()

try:
    while True:
        if future <= now:
            try:
                udp.sendto(msg_bytes, serveraddy)
                future = now + hole_time
            except socket.error as e:
                print(f"Initiating emergency stop due to {e}!")
                logging.getLogger("socket").info(f"Initiating emergency stop due to {e}!")
                wheels.full_stop()
                print(f"Socket error {e}, Retrying in 3 seconds")
                logging.getLogger("socket").info(f"Socket error {e}, Retrying in 3 seconds")
                time.sleep(3)
        
        ready_sockets, _, _ = select.select(
            [udp], [], [], hole_time
        )

        if ready_sockets:
            msgServer = udp.recv(buffSize)
            header = msgServer[0:len(options.CONTROL_HEADER)] if len(msgServer) > options.CONTROL_HEADER else None
            if header:
                msgServer = msgServer[len(options.CONTROL_HEADER):]
                values = [int.from_bytes(msgServer[i:i+2], 'little', signed=True) for i in range(0, len(msgServer), 2)]

            #checksum
            if header and reduce(lambda x, y: x ^ y, values[:-1]) == values[-1]:
                wheels.data_turn = values[0]
                wheels.data_speed = values[1]

                speed = .13
                if VIDEO:
                    syaw.value = syaw.value + values[4] * speed if abs(syaw.value + values[4] * speed) <= 1 else values[4]
                    spitch.value = spitch.value + values[5] * speed if abs(spitch.value + values[5] * speed) <= 1 else values[5]
                
            else:
                print('corrupt data', values[-1])
        else:
            print('no data')
            logging.getLogger('socket').info("Initiating emergency stop due to no data!")
            wheels.full_stop()
            
        now = time.time()
except:
    wheels.full_stop()
    if VIDEO:
        vsend.terminate()
        asend.terminate()
        vsend.kill()
        asend.kill()
    logging.getLogger('socket').exception('Exit due to:')
    sys.exit()





