#!/bin/python
from twisted.internet import reactor
from coapthon import defines
from coapthon.server.coap_protocol import CoAP
from example_resources import Storage, Separate, BasicResource, Long, Big

import twisted.internet.base
twisted.internet.base.DelayedCall.debug = True


class CoAPServer(CoAP):
    def __init__(self, host, port, multicast=False):
        CoAP.__init__(self, multicast)
        self.add_resource('basic/', BasicResource())
        self.add_resource('storage/', Storage())
        self.add_resource('separate/', Separate())
        self.add_resource('long/', Long())
        self.add_resource('big/', Big())
        print "CoAP Server start on " + host + ":" + str(port)
        # print(self.root.dump())


def main():
    server = CoAPServer("127.0.0.1", 5683)
    # reactor.listenMulticast(5683, server, listenMultiple=True)
    reactor.listenUDP(5683, server, "127.0.0.1")
    reactor.run()


if __name__ == '__main__':
    main()