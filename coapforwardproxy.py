import socket
import twisted
from twisted.internet import reactor
from twisted.python import log
from coapthon.client.coap_protocol import CoAP, HelperClient
from coapthon.proxy.forward_coap_protocol import ProxyCoAP

__author__ = 'giacomo'


class CoAPForwardProxy(ProxyCoAP):
    def __init__(self, host, port, client):
        ProxyCoAP.__init__(self, (host, port), client)
        print "CoAP Forward Proxy start on " + host + ":" + str(port)


def main():
    # portSocket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
    # # Make the port non-blocking and start it listening.
    # portSocket.setblocking(False)
    # portSocket.bind(('bbbb::2', 5683))
    #
    # # Now pass the port file descriptor to the reactor
    # port = reactor.adoptDatagramPort(
    #     portSocket.fileno(), socket.AF_INET6, CoAPForwardProxy("bbbb::2", 5683))
    #
    # # The portSocket should be cleaned up by the process that creates it.
    # portSocket.close()
    client = HelperClient(("bbbb::2", 5683), True)
    protocol = client.protocol

    reactor.listenUDP(5683, CoAPForwardProxy("bbbb::2", 5683, client), interface='bbbb::2')
    reactor.listenUDP(0, protocol, interface="bbbb::2")
    try:
        reactor.run()
    except twisted.internet.error.ReactorAlreadyRunning:
        log.err("CoAPForwardProxy - Reactor already started")
    except twisted.internet.error.ReactorNotRestartable:
        log.err("CoAPForwardProxy - Reactor not Restartable")


if __name__ == '__main__':
    main()