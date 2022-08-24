import math

from threading import Thread
from pygame.time import Clock
import sys
import socket
import os
from joysticks import get_controller
from functools import reduce


DIRECT_SOCKET = False # don't use the forwarding server?
if not DIRECT_SOCKET:
    addy = (os.getenv('FORWARDING_SERVER'), 25565) # forwarding server address

class ServerConnection(Thread):
    def __init__(self, controller, port):
        super(ServerConnection, self).__init__(daemon=True)
        self.contr = controller
        self.udp = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM, proto=socket.IPPROTO_UDP)
        self.udp.bind(("0.0.0.0", port))
    
    def run(self):
        if not DIRECT_SOCKET:
            global addy
        else:
            _, addy = self.udp.recvfrom(1024)
        clock = Clock()
        while True:
            msg = reduce(lambda x, y: x + y, self.contr.bytes()) \
            + (reduce(lambda x, y: x ^ y, self.contr)).to_bytes(2, 'little', signed=True)
            self.udp.sendto(msg, addy)
            clock.tick(60)

contr = get_controller()
serv = ServerConnection(contr, 25565)
serv.start()

clock = Clock()
while True:
    print(', '.join(f'{i}'.rjust(6) for i in contr), end='\r')

    if not contr.is_alive():
        print('PS4 Controller Exit')
        sys.exit()
    if not serv.is_alive():
        print('Socket Exit')
        sys.exit()
    clock.tick(30)