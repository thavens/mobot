from pydoc import cli
import socket
import logging
import sys

################################ Logger Settings #########################
logging.basicConfig(filename='client_daemon_log.txt',
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s> %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.NOTSET)
logging.info('Starting up')
###########################################################################

################################ Socket Setup #############################
keep_alive = "keep alive"
client_msg_bytes = str.encode(keep_alive)


server = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM, proto=socket.IPPROTO_UDP)
server.bind(('0.0.0.0', 25565))
###########################################################################

client_address = ('0.0.0.0', 9) # discard protocol

while True:
    try:
        bytes, addy = server.recvfrom(1024)
        if bytes == client_msg_bytes:
            if client_address != addy: print('new address', addy)
            client_address = addy
        else:
            server.sendto(bytes, client_address)
    except:
        logging.exception('Exit due to:')
        sys.exit()