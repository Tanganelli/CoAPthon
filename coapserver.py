#!/bin/python
from coapthon.server.coap_protocol import CoAP
from example_resources import Storage, Separate, BasicResource, Long, Big


class CoAPServer(CoAP):
    def __init__(self, host, port, multicast=False):
        CoAP.__init__(self, (host, port), multicast)
        self.add_resource('basic/', BasicResource())
        self.add_resource('storage/', Storage())
        self.add_resource('separate/', Separate())
        self.add_resource('long/', Long())
        self.add_resource('big/', Big())
        print "CoAP Server start on " + host + ":" + str(port)
        print(self.root.dump())


def main():
    server = CoAPServer("127.0.0.1", 5683)
    #reactor.listenMulticast(5683, server, listenMultiple=True)
    server.serve_forever()


if __name__ == '__main__':
    main()
