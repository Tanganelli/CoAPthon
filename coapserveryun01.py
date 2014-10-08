#!/bin/python
import httplib
from twisted.internet import reactor
from coapthon2 import defines
from coapthon2.resources.resource import Resource
from coapthon2.server.coap_protocol import CoAP
from example_resources import Storage, Separate

LIVINGROOM_LED_PIN = "4"
BEDROOM_LED_PIN = "7"
YUN1_IP = "192.168.0.16"

class CoAPServer(CoAP):
    def __init__(self, host, port, multicast=False):
        CoAP.__init__(self, multicast)
        self.add_resource('livingroom/light01/', Light(payload="Livingroom Light", pin=LIVINGROOM_LED_PIN, ip=YUN1_IP,
                                                       command="digital"))
        self.add_resource('bedroom/light01/', Light(payload="Bedroom Light", pin=BEDROOM_LED_PIN, ip=YUN1_IP,
                                                    command="digital"))
        print "CoAP Server start on " + host + ":" + str(port)
        print(self.root.dump())


def main():
    server = CoAPServer(YUN1_IP, 5683)
    #reactor.listenMulticast(5683, server, listenMultiple=True)
    reactor.listenUDP(5683, server, YUN1_IP)
    reactor.run()


if __name__ == '__main__':
    main()


class Light(Resource):
    def __init__(self, name="LightResource", payload="Light", pin="13", ip="127.0.0.1", command="digital"):
        super(Light, self).__init__(name, visible=True, observable=True, allow_children=False)
        self.payload = payload
        self.pin = pin
        self.ip = ip
        self.command = command

    def render_GET(self, request, query=None):
        return self.payload

    def render_PUT(self, request, payload=None, query=None):
        if payload is not None and payload == "on":
            conn = httplib.HTTPConnection(self.ip)
            path = "/arduino/" + self.command + "/" + self.pin + "/1"
            conn.request("GET", path)
            r1 = conn.getresponse()
            if r1.status == "200":
                print "Light ON"
        elif payload is not None and payload == "off":
            conn = httplib.HTTPConnection(self.ip)
            path = "/arduino/" + self.command + "/" + self.pin + "/0"
            conn.request("GET", path)
            r1 = conn.getresponse()
            if r1.status == "200":
                print "Light OFF"
        else:
            print "No valid Payload"

        return {"Payload": ""}