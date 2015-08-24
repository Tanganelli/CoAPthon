#!/bin/python
import getopt
import sys
from coapthon.server.coap_protocol import CoAP
from plugtest_resources import TestResource, SeparateResource


class CoAPServerPlugTest(CoAP):
    def __init__(self, host, port, multicast=False):
        CoAP.__init__(self, (host, port), multicast)
        self.add_resource('test/', TestResource())
        self.add_resource('separate/', SeparateResource())
        self.add_resource('seg1/', TestResource())
        self.add_resource('seg1/seg2/', TestResource())
        self.add_resource('seg1/seg2/seg3/', TestResource())
        self.add_resource('query/', TestResource())
        # print self.root.dump()


def usage():
    print "coapserverPlugTest.py -i <ip address> -p <port>"


def main(argv):
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

    server = CoAPServerPlugTest(ip, port)
    try:
        server.listen(10)
    except KeyboardInterrupt:
        print "Server Shutdown"
        server.close()
        print "Exiting..."


if __name__ == "__main__":
    main(sys.argv[1:])