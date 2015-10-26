from twisted.internet import reactor
from coapthon.proxy.forward_coap_protocol import ProxyCoAP

__author__ = 'giacomo'


class CoAPForwardProxy(ProxyCoAP):
    def __init__(self, host, port):
        ProxyCoAP.__init__(self, (host, port))
        print "CoAP Forward Proxy start on " + host + ":" + str(port)


def main():

    server = CoAPForwardProxy("bbbb::2", 5683)
    try:
        server.serve_forever(poll_interval=0.01)
    except KeyboardInterrupt:
        print "Server Shutdown"
        server.server_close()
        server.stopped.set()
        server.timer_mid.cancel()
        server.executor.shutdown(False)
        print "Exiting..."

if __name__ == '__main__':
    main()
