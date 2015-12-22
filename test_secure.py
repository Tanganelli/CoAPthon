import ssl
from socket import socket, AF_INET, SOCK_DGRAM
from dtls import do_patch
do_patch()
sock = ssl.wrap_socket(socket(AF_INET, SOCK_DGRAM))
sock.connect(('foo.bar.com', 1234))
sock.send('Hi there')