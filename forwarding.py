from pydoc import cli
import socket
import logging
import sys
import threading
import options

################################ Logger Settings #########################
logging.basicConfig(filename='client_daemon_log.txt',
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s> %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.NOTSET)
logging.info('Starting up')
###########################################################################

################################ Socket Setup #############################
client_msg_bytes = str.encode("client keep alive", 'ascii')
propogate_msg_bytes = str.encode('info update:', 'ascii')


server = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM, proto=socket.IPPROTO_UDP)
server.bind(('0.0.0.0', 25565))
###########################################################################

client_address = ('0.0.0.0', 9) # discard protocol
control_address = ('0.0.0.0', 9)

def video_forwarding():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('0.0.0.0', 25567))
    while True:
        msg, addy = sock.recvfrom(int(1e8))
        if addy[0] == client_address[0]:
            sock.sendto(msg, (control_address[0], 25567))

def audio_forwarding():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('0.0.0.0', 25568))
    while True:
        msg, addy = sock.recvfrom(int(1e8))
        if addy[0] == client_address[0]:
            sock.sendto(msg, (control_address[0], 25568))

if options.VIDEO:
    video = threading.Thread(target=video_forwarding, daemon=True)
    audio = threading.Thread(target=audio_forwarding, daemon=True)
    video.start()
    audio.start()


while True:
    try:
        bytes, addy = server.recvfrom(1024)
        if bytes == client_msg_bytes:
            if client_address != addy: print('new client address', addy)
            client_address = addy
        elif len(bytes) > len(propogate_msg_bytes) and bytes[:len(propogate_msg_bytes)] == propogate_msg_bytes:
            server.sendto(bytes, control_address)
        else:
            if control_address != addy: print('new control address', addy)
            control_address = addy
            server.sendto(bytes, client_address)
    except:
        logging.exception('Exit due to:')
        sys.exit()