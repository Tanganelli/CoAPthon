from twisted.internet import reactor
from coapthon.proxy.reverse_coap_proxy import ReverseProxyCoAP


__author__ = 'giacomo'


class CoAPReverseProxy(ReverseProxyCoAP):
    def __init__(self, host, port, file_xml):
        ReverseProxyCoAP.__init__(self, file_xml)
        print "CoAP Reverse Proxy start on " + host + ":" + str(port)


def main():
    proxy = CoAPReverseProxy("127.0.0.1", 5684, "reverse_proxy_mapping.xml")
    reactor.listenUDP(5684, proxy, "127.0.0.1")
    reactor.callInThread(proxy.parse_config())


if __name__ == '__main__':
    main()
