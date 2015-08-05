#!/bin/python
import getopt
import sys
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
        print self.root.with_prefix("/")


def usage():
    print "coapserver.py -i <ip address> -p <port>"


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

    server = CoAPServer(ip, port)
    try:
        server.serve_forever(poll_interval=0.01)
    except KeyboardInterrupt:
        print "Server Shutdown"
        server.server_close()
        server.stopped.set()
        server.executor_mid.cancel()
        server.executor.shutdown(False)
        print "Exiting..."


if __name__ == "__main__":
    main(sys.argv[1:])