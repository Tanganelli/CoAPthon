#!/usr/bin/env python

import getopt
import sys
from coapthon.reverse_proxy.coap import CoAP

__author__ = 'Giacomo Tanganelli'


class CoAPReverseProxy(CoAP):
    def __init__(self, host, port, xml_file, multicast=False, cache=False, starting_mid=None):
        CoAP.__init__(self, (host, port), xml_file=xml_file, multicast=multicast, starting_mid=starting_mid,
                      cache=cache)

        print "CoAP Proxy start on " + host + ":" + str(port)


def usage():  # pragma: no cover
    print "coapreverseproxy.py -i <ip address> -p <port> -f <xml_file>"


def main(argv):  # pragma: no cover
    ip = "0.0.0.0"
    port = 5684
    file_xml = "reverse_proxy_mapping.xml"
    try:
        opts, args = getopt.getopt(argv, "hi:p:f:", ["ip=", "port=", "file="])
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
        elif opt in ("-f", "--file"):
            file_xml = arg

    server = CoAPReverseProxy(ip, port, file_xml)
    try:
        server.listen(10)
    except KeyboardInterrupt:
        print "Server Shutdown"
        server.close()
        print "Exiting..."


if __name__ == "__main__":  # pragma: no cover
    main(sys.argv[1:])
