#!/bin/python
import httplib
from twisted.internet import reactor
from coapthon2.resources.resource import Resource
from coapthon2.server.coap_protocol import CoAP

LIVING_ROOM_LED_PIN = "12"
BEDROOM_LED_PIN1 = "11"
BEDROOM_LED_PIN2 = "10"
BATHROOM_LED_PIN = "9"
YUN1_IP = "192.168.240.1"


class Light(Resource):
    def __init__(self, name="LightResource", payload="Light", pin="13", ip="127.0.0.1", command="digital"):
        super(Light, self).__init__(name, visible=True, observable=True, allow_children=False)
        self.payload = payload
        self.pin = pin
        self.ip = ip
        self.command = command

    def render_GET(self, request=None, query=None):
        return self.payload

    def render_PUT(self, request=None, payload=None, query=None):
        if payload is not None and payload == "on":
            self.payload = "Light is on"
            print self.payload
            conn = httplib.HTTPConnection(self.ip)
            path = "/arduino/" + self.command + "/" + self.pin + "/1"
            conn.request("GET", path)
            r1 = conn.getresponse()
            if r1.status == "200":
                print "Light ON"
        elif payload is not None and payload == "off":
            self.payload = "Light is off"
            print self.payload
            conn = httplib.HTTPConnection(self.ip)
            path = "/arduino/" + self.command + "/" + self.pin + "/0"
            conn.request("GET", path)
            r1 = conn.getresponse()
            if r1.status == "200":
                print "Light OFF"
        else:
            print "No valid Payload"

        return {"Payload": ""}


class Servo(Resource):
    def __init__(self, name="ServoResource", payload="Servo", pin="13", ip="127.0.0.1", command="servo"):
        super(Servo, self).__init__(name, visible=True, observable=True, allow_children=False)
        self.payload = payload
        self.pin = pin
        self.ip = ip
        self.command = command

    def render_GET(self, request=None, query=None):
        return self.payload

    def render_PUT(self, request=None, payload=None, query=None):
        print payload
        if payload is not None and payload == "open":
            self.payload = "Garage Door is open"
            conn = httplib.HTTPConnection(self.ip)
            path = "/arduino/" + self.command + "/" + self.pin + "/60"
            conn.request("GET", path)
            r1 = conn.getresponse()
            if r1.status == "200":
                print "Door Opened"
        elif payload is not None and payload == "close":
            self.payload = "Garage Door is close"
            conn = httplib.HTTPConnection(self.ip)
            path = "/arduino/" + self.command + "/" + self.pin + "/180"
            conn.request("GET", path)
            r1 = conn.getresponse()
            if r1.status == "200":
                print "Door Closed"
        else:
            print "No valid Payload"

        return {"Payload": ""}


class CoAPServer(CoAP):
    def __init__(self, host, port, multicast=False):
        CoAP.__init__(self, multicast)
        self.add_resource('light01/', Light(payload="Living Room Light", pin=LIVING_ROOM_LED_PIN, ip=YUN1_IP,
                                            command="digital"))
        self.add_resource('light02/', Light(payload="Bedroom Light", pin=BEDROOM_LED_PIN1, ip=YUN1_IP,
                                            command="digital"))
        self.add_resource('light03/', Light(payload="Bedroom Light", pin=BEDROOM_LED_PIN2, ip=YUN1_IP,
                                            command="digital"))
        self.add_resource('light04/', Light(payload="Bathroom Light", pin=BATHROOM_LED_PIN, ip=YUN1_IP,
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


