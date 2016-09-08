#!/usr/bin/env python

import getopt
import sys
from coapthon.resources.resource import Resource
from coapthon.server.coap import CoAP
from exampleresources import BasicResource, Long, Separate, Storage, Big, voidResource, XMLResource, ETAGResource, Child, \
    MultipleEncodingResource
from plugtest_resources import ObservableResource

__author__ = 'giacomo'


class CoAPServer(CoAP):
    def __init__(self, host, port, multicast=False):
        CoAP.__init__(self, (host, port), multicast)
        self.add_resource('basic/', BasicResource())
        self.add_resource('storage/', Storage())
        self.add_resource('separate/', Separate())
        self.add_resource('long/', Long())
        self.add_resource('big/', Big())
        self.add_resource('void/', voidResource())
        self.add_resource('xml/', XMLResource())
        self.add_resource('encoding/', MultipleEncodingResource())
        self.add_resource('etag/', ETAGResource())
        self.add_resource('child/', Child())

        print "CoAP Server start on " + host + ":" + str(port)
        print self.root.dump()


def usage():  # pragma: no cover
    print "coapserver.py -i <ip address> -p <port>"


def main(argv):  # pragma: no cover
    ip = "127.0.0.1"
    port = 5683
    try:
        opts, args = getopt.getopt(argv, "hi:p:", ["ip=", "port="])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            usage()
            sys.exit()
        elif opt in ("-i", "--ip"):
            ip = arg
        elif opt in ("-p", "--port"):
            port = int(arg)

    server = CoAPServer(ip, port)
    try:
        server.listen(10)
    except KeyboardInterrupt:
        print "Server Shutdown"
        server.close()
        print "Exiting..."


if __name__ == "__main__":  # pragma: no cover
    main(sys.argv[1:])
