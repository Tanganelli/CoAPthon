#!/bin/python
from twisted.internet import reactor
from coapthon2 import defines
from coapthon2.server.coap_protocol import CoAP
from example_resources import Storage, Separate


class CoAPServer(CoAP):
    def __init__(self, host, port, multicast=False):
        CoAP.__init__(self, multicast)
        self.add_resource('storage/', Storage())
        self.add_resource('separate/', Separate())
        print "CoAP Server start on " + host + ":" + str(port)
        print(self.root.dump())


def main():
    server = CoAPServer("127.0.0.1", 5683)
    #reactor.listenMulticast(5683, server, listenMultiple=True)
    reactor.listenUDP(5683, server, "127.0.0.1")
    reactor.run()


if __name__ == '__main__':
    main()
