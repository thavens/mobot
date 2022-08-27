from dataclasses import dataclass
import math

import threading
from threading import Thread
import pygame
from pygame.time import Clock
import pygame.locals
import sys
import socket
import os
from joysticks import get_controller
from functools import reduce
import traceback
from video import video_listen, audio_listen
from typing import Tuple

DIRECT_SOCKET = False # don't use the forwarding server?
VIDEO = False # Use webcam?

@dataclass
class Addy(threading.Event):
    address: Tuple[str, int]

if not DIRECT_SOCKET:
    addy = Addy((os.getenv('FORWARDING_SERVER'), 25565)) # forwarding server address
    addy.set()
else:
    addy = Addy(None)

class ServerConnection(Thread):
    def __init__(self, controller, addy:Addy, udp:socket.socket):
        super(ServerConnection, self).__init__(daemon=True)
        self.contr = controller
        self.udp = udp
        self.addy = addy
    
    def run(self):
        self.addy.wait()
        clock = Clock()
        while True:
            msg = reduce(lambda x, y: x + y, self.contr.bytes()) \
            + (reduce(lambda x, y: x ^ y, self.contr)).to_bytes(2, 'little', signed=True)
            self.udp.sendto(msg, self.addy.address)
            clock.tick(60)
            

@dataclass
class ControlListener(Thread):
    addy: Addy
    udp: socket.socket
    def __init__(self, addy:Addy, udp:socket.socket):
        super(ControlListener, self).__init__(daemon=True)
        self.addy = addy
        self.udp = udp
        self.propogate_msg_bytes = str.encode('info update:', 'ascii')
        self.data = [0] * 6
    
    def run(self):
        while 1:
            msg, addy.address = self.udp.recvfrom(1024)
            addy.set()
            if len(msg) > len(self.propogate_msg_bytes) and msg[:len(self.propogate_msg_bytes)] == self.propogate_msg_bytes and len(data := msg[len(self.propogate_msg_bytes):]) == 18:
                # drop msg header through if statement
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
                    self.data = incoming[1:]
                else:
                    print('got corrupt data from client/forwarding server.')

class Display:
    def __init__(self):
        self.BLACK = (0, 0, 0)
        self.WHITE = (200, 200, 200)
        pygame.init()
        self.screen = pygame.display.set_mode((640, 240))
        self.font = pygame.font.SysFont('ubuntumono', 20)
        self.running = True
        self.x = 20
        self.y = 20
    
    def writeLine(self, text):
        rendered = self.font.render(text, True, self.BLACK)
        self.screen.blit(rendered, (self.x, self.y))
        self.y += 20
    
    def reset(self):
        self.x = 20
        self.y = 20
        self.screen.fill(self.WHITE)

        for event in pygame.event.get():
            if event.type == pygame.locals.QUIT:
                self.running = False
    
    def update(self):
        pygame.display.update()

contr = get_controller()
udp = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM, proto=socket.IPPROTO_UDP)
udp.bind(("0.0.0.0", 25565))

# insantiate the listening thread
listener = ControlListener(addy)
serv = ServerConnection(contr, addy, udp)
# start the listening thread
listener.start()
serv.start()

display = Display()
clock = Clock()
input_label = 'Input data:'
robot_data_label = 'Robot data:'
try:
    if VIDEO:
        vlisten = video_listen()
        alisten = audio_listen()
    while display.running:
        display.reset()
        display.writeLine(input_label)
        display.writeLine(', '.join(f'{i}'.rjust(6) for i in ['turn', 'speed', 'N/A', 'N/A', 'Yaw', 'Pitch']))
        display.writeLine(', '.join(f'{i}'.rjust(6) for i in contr))
        display.writeLine(robot_data_label)
        display.writeLine(', '.join(f'{i}'.rjust(6) for i in ['cmd1', 'cmd2', 'speedR_meas', 'speedL_meas', 'batVoltage', 'boardTemp']))
        display.writeLine(', '.join(f'{i}'.rjust(6) for i in listener.data))
        display.update()

        if not contr.is_alive():
            print('PS4 Controller Exit')
            sys.exit()
        if not serv.is_alive():
            print('Socket Exit')
            sys.exit()
        clock.tick(30)
except:
    if VIDEO:
        vlisten.terminate()
        alisten.terminate()
        vlisten.kill()
        alisten.kill()
    traceback.print_exc()