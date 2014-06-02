from twisted.internet import reactor
from twisted.python import log
from coapthon2.server.coap_protocol import CoAP
from esample_resources import Storage


class CoAPServer(CoAP):
    def __init__(self):
        CoAP.__init__(self)
        if self.add_resource('storage/', Storage()):
            log.msg(self.root.dump())


def main():
    reactor.listenUDP(5683, CoAPServer())
    reactor.run()


if __name__ == '__main__':
    main()
