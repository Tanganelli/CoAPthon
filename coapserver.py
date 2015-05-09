#!/bin/python
import os
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


def main():
    server = CoAPServer("127.0.0.1", 5683)
    try:
        server.serve_forever(poll_interval=0.01)
    except KeyboardInterrupt:
        print "Server Shutdown"
        server.server_close()
        server.stopped.set()
        server.executor_mid.shutdown(False)
        server.executor.shutdown(False)
        print "Exiting..."
    finally:
        os._exit(0)

if __name__ == '__main__':
    main()
