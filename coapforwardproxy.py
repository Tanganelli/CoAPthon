from twisted.internet import reactor
from coapthon.proxy.forward_coap_protocol import ProxyCoAP

__author__ = 'giacomo'


class CoAPForwardProxy(ProxyCoAP):
    def __init__(self, host, port):
        ProxyCoAP.__init__(self)
        print "CoAP Forward Proxy start on " + host + ":" + str(port)


def main():
    reactor.listenUDP(5684, CoAPForwardProxy("127.0.0.1", 5684), "127.0.0.1")
    reactor.run()


if __name__ == '__main__':
    main()