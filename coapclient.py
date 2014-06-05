#!/bin/python
from twisted.internet import reactor
from coapthon2.client.coap_protocol import CoAP


def main():
    protocol = CoAP()
    function = protocol.get
    args = ("/hello",)
    kwargs = {}
    protocol.set_operations([(function, args, kwargs)])
    t = reactor.listenUDP(0, protocol)
    reactor.run()


if __name__ == '__main__':
    main()