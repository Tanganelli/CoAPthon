import socket
from twisted.internet import reactor
from coapthon.proxy.forward_coap_protocol import ProxyCoAP

__author__ = 'giacomo'


class CoAPForwardProxy(ProxyCoAP):
    def __init__(self, host, port):
        ProxyCoAP.__init__(self)
        print "CoAP Forward Proxy start on " + host + ":" + str(port)


def main():
    portSocket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
    # Make the port non-blocking and start it listening.
    portSocket.setblocking(False)
    portSocket.bind(('bbbb::2', 5683))

    # Now pass the port file descriptor to the reactor
    port = reactor.adoptDatagramPort(
        portSocket.fileno(), socket.AF_INET6, CoAPForwardProxy("bbbb::2", 5683))

    # The portSocket should be cleaned up by the process that creates it.
    portSocket.close()

    #reactor.listenUDP(5683, CoAPForwardProxy("bbbb::2", 5683), "bbbb::2")
    reactor.run()


if __name__ == '__main__':
    main()