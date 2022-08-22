from distutils.log import info
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

############ Client Options #########
hole_time = 1 #seconds
keep_alive = "keep alive"
msg_bytes = str.encode(keep_alive)
serveraddy = (os.getenv('FORWARDING_SERVER'), 25565)
buffSize = 1024
#####################################

######### Daemon Options ############
START_FRAME = 0xABCD
TIME_SEND = 0.05
log_interval = 10
#####################################

######### Logger Options ############
logging.basicConfig(filename='client_daemon_log.txt',
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s> %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.NOTSET)
logging.info('Starting up')
#####################################


udp = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM, proto=socket.IPPROTO_UDP)
udp.bind(('0.0.0.0', 25566))
udp.setblocking(False)

now = time.time()
future = now

################################################### Daemon Setup ############################################
brecieve = ['cmd1', 'cmd2', 'speedR_meas', 'speedL_meas', 'batVoltage', 'boardTemp']

@dataclass
class Wheels:
    data_speed: int
    data_turn: int

def target(data: Wheels):
    def send(speed, steer):
        msg = START_FRAME.to_bytes(2, 'little') \
            + steer.to_bytes(2, 'little', signed=True) \
            + speed.to_bytes(2, 'little', signed=True) \
            + ct.c_uint16(START_FRAME ^ steer ^ speed).value.to_bytes(2, 'little')
        front.write(msg)

    def receive():
        if front.in_waiting:
            data = front.read_all()
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

                if reduce(lambda x, y: x ^ y, incoming) == checksum:
                    if incoming[5] == 30:
                        logging.getLogger('daemon').info('Low Battery Exit')
                        sys.exit()
                    if receive.time_log < (now := time.time()):
                        receive.time_log = now + log_interval
                        logging.getLogger('daemon').info(
                            ' '.join([i + ': ' + j for i, j in zip(brecieve, incoming[1:])])
                        )

    try:
        front = serial.Serial('/dev/ttyUSB0', baudrate=115200, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE)
        itime_send = 0
        receive.time_log = 0
        while True:
            now = time.time()
            receive()

            if itime_send < now:
                itime_send = now + TIME_SEND
                send(data.data_turn, data.data_speed)
    except:
        logging.getLogger('daemon').exception('Exit due to:')
        sys.exit()

front = Wheels(0, 0)
thread = Thread(target=target, args=(front,))
thread.start()

while True:
    try:
        if future <= now:
            udp.sendto(msg_bytes, serveraddy)
            future = now + hole_time
        
        ready_sockets, _, _ = select.select(
            [udp], [], [], hole_time
        )

        if ready_sockets:
            msgServer = udp.recv(buffSize)
            values = [int.from_bytes(msgServer[i:i+2], 'little', signed=True) for i in range(0, len(msgServer), 2)]

            #checksum
            if reduce(lambda x, y: x ^ y, values[:-1]) == values[-1]:
                front.data_turn = int(values[0] / 65.534)
                front.data_speed = int(values[1] / 65.534)
                print(values[1], front.data_turn, values[3], front.data_speed)
            else:
                print('corrupt data', values[-1])
        else:
            print('no data')
            front.data_turn = 0
            front.data_speed = 0
        
        now = time.time()
    except:
        logging.getLogger('socket').exception('Exit due to:')
        sys.exit()





