import math
from pyPS4Controller.controller import Controller
from threading import Thread
from time import sleep
import sys
import socket
import os

CUBE_CONTROL = False # cubed throttle control
DIRECT_SOCKET = False # don't use the forwarding server?
if not DIRECT_SOCKET:
    addy = (os.getenv('FORWARDING_SERVER'), 25565) # forwarding server address

class MyController(Controller):
    def __init__(self, **kwargs) :
        super(MyController, self).__init__(**kwargs)
        self.L3_vert = 0
        self.L3_horiz = 0
        self.R3_vert = 0
        self.R3_horiz = 0
    
    def on_L3_up(self, value):
        self.L3_vert = -value
        if CUBE_CONTROL:
            self.cube_control('L3_vert')
    
    def on_L3_down(self, value):
        self.L3_vert = -value
        if CUBE_CONTROL:
            self.cube_control('L3_vert')
    
    def on_L3_right(self, value):
        self.L3_horiz = value
        if CUBE_CONTROL:
            self.cube_control('L3_horiz')
    
    def on_L3_left(self, value):
        self.L3_horiz = value
        if CUBE_CONTROL:
            self.cube_control('L3_horiz')
    
    def on_L3_y_at_rest(self):
        self.L3_vert = 0

    def on_L3_x_at_rest(self):
        self.L3_horiz = 0
    
    def on_R3_up(self, value):
        self.R3_vert = -value
        if CUBE_CONTROL:
            self.cube_control('R3_vert')
    
    def on_R3_down(self, value):
        self.R3_vert = -value
        if CUBE_CONTROL:
            self.cube_control('R3_vert')
    
    def on_R3_right(self, value):
        self.R3_horiz = value
        if CUBE_CONTROL:
            self.cube_control('R3_horiz')
    
    def on_R3_left(self, value):
        self.R3_horiz = value
        if CUBE_CONTROL:
            self.cube_control('R3_horiz')
    
    def on_R3_y_at_rest(self):
        self.R3_vert = 0
    
    def on_R3_x_at_rest(self):
        self.R3_horiz = 0
    
    def cube_control(self, value_name):
        reg = self.__getattribute__(value_name) / 32767
        reg **= 3
        reg *= 32767
        self.__setattr__(value_name, int(reg))

class ServerConnection(Thread):
    def __init__(self, controller, port):
        super(ServerConnection, self).__init__(daemon=True)
        self.contr = controller
        self.udp = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM, proto=socket.IPPROTO_UDP)
        self.udp.bind(("0.0.0.0", port))
    
    def run(self):
        if DIRECT_SOCKET:
            _, addy = self.udp.recvfrom(1024)
        while True:
            sleep(0.05)
            msg = self.contr.L3_horiz.to_bytes(2, 'little', signed=True) \
            + self.contr.L3_vert.to_bytes(2, 'little', signed=True) \
            + self.contr.R3_horiz.to_bytes(2, 'little', signed=True) \
            + self.contr.R3_vert.to_bytes(2, 'little', signed=True) \
            + ((self.contr.L3_horiz ^ self.contr.L3_vert ^ self.contr.R3_horiz ^ self.contr.R3_vert)).to_bytes(2, 'little', signed=True)
            self.udp.sendto(msg, addy)


contr = MyController(interface="/dev/input/js0", connecting_using_ds4drv=False)
thread = Thread(target=contr.listen, daemon=True)
thread.start()

serv = ServerConnection(contr, 25565)
serv.start()

while True:
    sleep(0.1)
    print(contr.L3_horiz, contr.L3_vert, contr.R3_horiz, contr.R3_vert, end='\r')

    if not thread.is_alive():
        print('PS4 Controller Exit')
        sys.exit()
    if not serv.is_alive():
        print('Socket Exit')
        sys.exit()