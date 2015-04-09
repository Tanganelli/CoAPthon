#!/bin/python
import httplib
from twisted.internet import reactor
from coapthon.resources.resource import Resource
from coapthon.server.coap_protocol import CoAP

GARDEN_LED_PIN1 = "12"
GARDEN_LED_PIN2 = "11"
ALARM_PIN = "7"
FAN_PIN = "9"
GARAGE_PIN = "5"
DININGROOM_LED_PIN = "7"
YUN2_IP = "192.168.240.239"


class Fan(Resource):
    def __init__(self, name="FanResource", payload="Fan", pin="13", ip="127.0.0.1", command="digital"):
        super(Fan, self).__init__(name, visible=True, observable=True, allow_children=False)
        self.payload = payload
        self.pin = pin
        self.ip = ip
        self.command = command

    def render_GET(self, request=None, query=None):
        return self.payload

    def render_PUT(self, request=None, payload=None, query=None):
        print payload
        if payload is not None and payload == "on":
            self.payload = "Fan is on"
            conn = httplib.HTTPConnection(self.ip)
            path = "/arduino/" + self.command + "/" + self.pin + "/1"
            conn.request("GET", path)
            r1 = conn.getresponse()
            if r1.status == "200":
                print "Fan ON"
        elif payload is not None and payload == "off":
            self.payload = "Fan is off"
            conn = httplib.HTTPConnection(self.ip)
            path = "/arduino/" + self.command + "/" + self.pin + "/0"
            conn.request("GET", path)
            r1 = conn.getresponse()
            if r1.status == "200":
                print "Fan OFF"
        else:
            print "No valid Payload"

        return {"Payload": self.payload}


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
        print payload
        if payload is not None and payload == "on":
            self.payload = "Light is on"
            conn = httplib.HTTPConnection(self.ip)
            path = "/arduino/" + self.command + "/" + self.pin + "/1"
            conn.request("GET", path)
            r1 = conn.getresponse()
            if r1.status == "200":
                print "Light ON"
        elif payload is not None and payload == "off":
            self.payload = "Light is off"
            conn = httplib.HTTPConnection(self.ip)
            path = "/arduino/" + self.command + "/" + self.pin + "/0"
            conn.request("GET", path)
            r1 = conn.getresponse()
            if r1.status == "200":
                print "Light OFF"
        else:
            print "No valid Payload"

        return {"Payload": self.payload}


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

        return {"Payload": self.payload}


class Alarm(Resource):
    def __init__(self, name="AlarmResource", payload="Alarm", pin="7", ip="127.0.0.1", command="alarm"):
        super(Alarm, self).__init__(name, visible=True, observable=True, allow_children=False)
        self.payload = payload
        self.pin = pin
        self.ip = ip
        self.command = command
        self.status = False
        self.statusstring = "Door is close"

    def render_GET(self, request=None, query=None):
        return self.statusstring

    def render_PUT(self, request=None, payload=None, query=None):
        if payload is not None and payload == "open":
            self.statusstring = "Door is open"
        elif payload is not None and payload == "close":
            self.statusstring = "Door is close"

        else:
            print "No valid Payload"

        return {"Payload": self.payload}


class CoAPServer(CoAP):
    def __init__(self, host, port, multicast=False):
        CoAP.__init__(self, multicast)
        self.add_resource('garden01/', Light(payload="Garden Light 01", pin=GARDEN_LED_PIN1, ip=YUN2_IP,
                                             command="digital"))
        self.add_resource('garden02/', Light(payload="Garden Light 02", pin=GARDEN_LED_PIN2, ip=YUN2_IP,
                                             command="digital"))
        self.add_resource('garage/', Servo(payload="Garage Door", pin=GARAGE_PIN, ip=YUN2_IP,
                                           command="servo"))
        self.add_resource('alarm/', Alarm(payload="Alarm", pin=ALARM_PIN, ip=YUN2_IP,
                                          command="digital"))
        self.add_resource('fan/', Fan(payload="Alarm", pin=FAN_PIN, ip=YUN2_IP,
                                        command="digital"))
        self.add_resource('light01/', Light(payload="Bathroom Light", pin=DININGROOM_LED_PIN, ip=YUN2_IP,
                                            command="digital"))
        print "CoAP Server start on " + host + ":" + str(port)
        print(self.root.dump())


def main():
    server = CoAPServer(YUN2_IP, 5683)
    #reactor.listenMulticast(5683, server, listenMultiple=True)
    reactor.listenUDP(5683, server, YUN2_IP)
    reactor.run()


if __name__ == '__main__':
    main()


