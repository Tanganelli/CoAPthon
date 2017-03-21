#!/usr/bin/env python

import getopt
import sys
from coapthon.forward_proxy.coap import CoAP

__author__ = 'Giacomo Tanganelli'


class CoAPForwardProxy(CoAP):
    def __init__(self, host, port,  multicast=False):
        CoAP.__init__(self, (host, port), multicast=multicast)

        print "CoAP Proxy start on " + host + ":" + str(port)


def usage():  # pragma: no cover
    print "coapforwardproxy.py -i <ip address> -p <port>"


def main(argv):  # pragma: no cover
    ip = "0.0.0.0"
    port = 5684
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

    server = CoAPForwardProxy(ip, port)
    try:
        server.listen(10)
    except KeyboardInterrupt:
        print "Server Shutdown"
        server.close()
        print "Exiting..."


if __name__ == "__main__":  # pragma: no cover
    main(sys.argv[1:])
