from coapthon import defines
from coapthon.client.coap_synchronous import HelperClientSynchronous
from coapthon.messages.request import Request
from coapthon.resources.resource import Resource
from twisted.internet import reactor
from coapthon.server.coap_protocol import CoAP

import RPi.GPIO as GPIO


def callback(channel):
    client = HelperClientSynchronous()
    client.put({"path": "coap://127.0.0.1:5683/pin1", "payload": GPIO.input(channel)})


class RPiResource(Resource):
    channel = 0
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(channel, GPIO.IN)
    GPIO.add_event_detect(channel, GPIO.RISING, callback=callback)

    def render_GET(self, request):
        self.payload = GPIO.input(self.channel)
        return self

    def render_PUT(self, request):
        self.payload = request.payload
        return self


class CoAPServer(CoAP):
    def __init__(self, host, port, multicast=False):
        CoAP.__init__(self, multicast)
        self.add_resource('temp/', RPiResource("channel0"))

        print "CoAP Server start on " + host + ":" + str(port)
        print(self.root.dump())


def main():
    server = CoAPServer("127.0.0.1", 5683)
    #reactor.listenMulticast(5683, server, listenMultiple=True)
    reactor.listenUDP(5683, server, "127.0.0.1")
    reactor.run()


if __name__ == '__main__':
    main()
