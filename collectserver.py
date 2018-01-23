#!/usr/bin/env python

import getopt
import json
import random
import sys
import threading

import time

from coapthon import defines
from coapthon.resources.resource import Resource
from coapthon.server.coap import CoAP


__author__ = 'Giacomo Tanganelli'


class PowerResource(Resource):
    def __init__(self, name="PowerResource", coap_server=None):
        super(PowerResource, self).__init__(name, coap_server, visible=True,
                                            observable=True, allow_children=False)
        self.resource_type = "Power Resource"
        self.content_type = "application/json"
        self.cpu_power = 0
        self.lpm_power = 0
        self.listen_power = 0
        self.transmit_power = 0
        self.average_power = 0
        self.aggregate_power = 0
        self.period = 5
        self.read_sensor(True)

        self.value = [{"n": "cpu", "v": self.cpu_power, "u": "mW", "bt": time.time()},
                      {"n": "lpm", "v": self.lpm_power, "u": "mW"},
                      {"n": "listen", "v": self.listen_power, "u": "mW"},
                      {"n": "transmit", "v": self.transmit_power, "u": "mW"},
                      {"n": "average", "v": self.average_power, "u": "mW"},
                      {"n": "aggregate", "v": self.aggregate_power, "u": "mW"}]

    def render_GET(self, request):
        self.value = [{"n": "cpu", "v": self.cpu_power, "u": "mW", "bt": time.time()},
                      {"n": "lpm", "v": self.lpm_power, "u": "mW"},
                      {"n": "listen", "v": self.listen_power, "u": "mW"},
                      {"n": "transmit", "v": self.transmit_power, "u": "mW"},
                      {"n": "average", "v": self.average_power, "u": "mW"},
                      {"n": "aggregate", "v": self.aggregate_power, "u": "mW"}]

        self.payload = (defines.Content_types["application/json"], json.dumps(self.value))
        return self

    def read_sensor(self, first=False):
        self.cpu_power = random.uniform(0, 0.3)
        self.lpm_power = random.uniform(0, 0.15)
        self.listen_power = random.uniform(0, 0.4)
        self.transmit_power = random.uniform(0, 0.2)
        self.average_power = 0
        self.aggregate_power = self.cpu_power + self.lpm_power + self.listen_power + self.transmit_power

        self.value = [{"n": "cpu", "v": self.cpu_power, "u": "mW", "bt": time.time()},
                      {"n": "lpm", "v": self.lpm_power, "u": "mW"},
                      {"n": "listen", "v": self.listen_power, "u": "mW"},
                      {"n": "transmit", "v": self.transmit_power, "u": "mW"},
                      {"n": "average", "v": self.average_power, "u": "mW"},
                      {"n": "aggregate", "v": self.aggregate_power, "u": "mW"}]

        self.payload = (defines.Content_types["application/json"], json.dumps(self.value))
        if not self._coap_server.stopped.isSet():

            timer = threading.Timer(self.period, self.read_sensor)
            timer.setDaemon(True)
            timer.start()

            if not first and self._coap_server is not None:
                self._coap_server.notify(self)
                self.observe_count += 1


class TemperatureResource(Resource):
    def __init__(self, name="TemperatureResource", coap_server=None):
        super(TemperatureResource, self).__init__(name, coap_server, visible=True,
                                                  observable=True, allow_children=False)
        self.resource_type = "Temperature Resource"
        self.content_type = "application/json"
        self.temperature = 0
        self.period = 5
        self.read_sensor(True)

        self.value = [{"n": "temperature", "v": self.temperature, "u": "Cel", "t": time.time()}]

    def render_GET(self, request):
        self.value = [{"n": "temperature", "v": self.temperature, "u": "Cel", "t": time.time()}]

        self.payload = (defines.Content_types["application/json"], json.dumps(self.value))
        return self

    def read_sensor(self, first=False):
        self.temperature = random.uniform(-10, 30)

        self.value = [{"n": "temperature", "v": self.temperature, "u": "Cel", "t": time.time()}]

        self.payload = (defines.Content_types["application/json"], json.dumps(self.value))
        if not self._coap_server.stopped.isSet():

            timer = threading.Timer(self.period, self.read_sensor)
            timer.setDaemon(True)
            timer.start()

            if not first and self._coap_server is not None:
                self._coap_server.notify(self)
                self.observe_count += 1


class BatteryResource(Resource):
    def __init__(self, name="BatteryResource", coap_server=None):
        super(BatteryResource, self).__init__(name, coap_server, visible=True,
                                              observable=True, allow_children=False)
        self.resource_type = "Battery Resource"
        self.content_type = "application/json"
        self.voltage = 0
        self.indicator = 0
        self.period = 5
        self.read_sensor(True)

        self.value = [{"n": "voltage", "v": self.voltage, "u": "V", "bt": time.time()},
                      {"n": "indicator", "v": self.indicator, "u": "%"}]

    def render_GET(self, request):
        self.value = [{"n": "voltage", "v": self.voltage, "u": "V", "bt": time.time()},
                      {"n": "indicator", "v": self.indicator, "u": "%"}]

        self.payload = (defines.Content_types["application/json"], json.dumps(self.value))
        return self

    def read_sensor(self, first=False):
        self.voltage = random.uniform(0, 5)
        self.indicator = random.randint(1, 10)

        self.value = [{"n": "voltage", "v": self.voltage, "u": "V", "bt": time.time()},
                      {"n": "indicator", "v": self.indicator, "u": "%"}]

        self.payload = (defines.Content_types["application/json"], json.dumps(self.value))
        if not self._coap_server.stopped.isSet():

            timer = threading.Timer(self.period, self.read_sensor)
            timer.setDaemon(True)
            timer.start()

            if not first and self._coap_server is not None:
                self._coap_server.notify(self)
                self.observe_count += 1


class RadioResource(Resource):
    def __init__(self, name="RadioResource", coap_server=None):
        super(RadioResource, self).__init__(name, coap_server, visible=True,
                                            observable=True, allow_children=False)
        self.resource_type = "Radio Resource"
        self.content_type = "application/json"
        self.rssi = 0
        self.latency = 0
        self.best_neighbor_id = "0"
        self.best_neighbor_etx = 0
        self.byte_sent = 0
        self.byte_received = 0
        self.period = 5
        self.read_sensor(True)

        self.value = [{"n": "rssi", "v": self.rssi, "u": "dBm", "bt": time.time()},
                      {"n": "latency", "v": self.latency, "u": "ms"},
                      {"n": "best_neighbor_id", "vs": self.best_neighbor_id},
                      {"n": "best_neighbor_etx", "v": self.best_neighbor_etx},
                      {"n": "byte_sent", "v": self.byte_sent},
                      {"n": "byte_received", "v": self.byte_received}]

    def render_GET(self, request):
        self.value = [{"n": "rssi", "v": self.rssi, "u": "dBm", "bt": time.time()},
                      {"n": "latency", "v": self.latency, "u": "ms"},
                      {"n": "best_neighbor_id", "vs": self.best_neighbor_id},
                      {"n": "best_neighbor_etx", "v": self.best_neighbor_etx},
                      {"n": "byte_sent", "v": self.byte_sent},
                      {"n": "byte_received", "v": self.byte_received}]

        self.payload = (defines.Content_types["application/json"], json.dumps(self.value))
        return self

    def read_sensor(self, first=False):
        self.rssi = random.uniform(-90, -10)
        self.latency = random.uniform(0, 50)
        self.best_neighbor_id = "0"
        self.best_neighbor_etx = random.randint(1, 10)
        self.byte_sent = random.randint(1, 500)
        self.byte_received = random.randint(1, 500)

        self.value = [{"n": "rssi", "v": self.rssi, "u": "dBm", "bt": time.time()},
                      {"n": "latency", "v": self.latency, "u": "ms"},
                      {"n": "best_neighbor_id", "vs": self.best_neighbor_id},
                      {"n": "best_neighbor_etx", "v": self.best_neighbor_etx},
                      {"n": "byte_sent", "v": self.byte_sent},
                      {"n": "byte_received", "v": self.byte_received}]
        self.payload = (defines.Content_types["application/json"], json.dumps(self.value))

        if not self._coap_server.stopped.isSet():

            timer = threading.Timer(self.period, self.read_sensor)
            timer.setDaemon(True)
            timer.start()

            if not first and self._coap_server is not None:
                self._coap_server.notify(self)
                self.observe_count += 1

class HumidityResource(Resource):
    def __init__(self, name="HumidityResource", coap_server=None):
        super(HumidityResource, self).__init__(name, coap_server, visible=True,
                                               observable=True, allow_children=False)
        self.resource_type = "Humidity Resource"
        self.content_type = "application/json"
        self.humidity = 0
        self.period = 5
        self.read_sensor(True)

        self.value = [{"n": "humidity", "v": self.humidity, "u": "%RH", "t": time.time()}]

    def render_GET(self, request):
        self.value = [{"n": "humidity", "v": self.humidity, "u": "%RH", "t": time.time()}]

        self.payload = (defines.Content_types["application/json"], json.dumps(self.value))
        return self

    def read_sensor(self, first=False):
        self.humidity = random.randint(0, 100)

        self.value = [{"n": "humidity", "v": self.humidity, "u": "%RH", "t": time.time()}]
        self.payload = (defines.Content_types["application/json"], json.dumps(self.value))
        if not self._coap_server.stopped.isSet():

            timer = threading.Timer(self.period, self.read_sensor)
            timer.setDaemon(True)
            timer.start()

            if not first and self._coap_server is not None:
                self._coap_server.notify(self)
                self.observe_count += 1


class LightResource(Resource):
    def __init__(self, name="LightResource", coap_server=None):
        super(LightResource, self).__init__(name, coap_server, visible=True,
                                            observable=True, allow_children=False)
        self.resource_type = "Light Resource"
        self.content_type = "application/json"
        self.light1 = 0
        self.light2 = 0

        self.value = [{"n": "light1", "v": self.light1, "u": "lx", "bt": time.time()},
                      {"n": "light2", "v": self.light2, "u": "lx"}]
        self.period = 5
        self.read_sensor(True)

    def render_GET(self, request):
        self.value = [{"n": "light1", "v": self.light1, "u": "lx", "bt": time.time()},
                      {"n": "light2", "v": self.light2, "u": "lx"}]

        self.payload = (defines.Content_types["application/json"], json.dumps(self.value))
        return self

    def read_sensor(self, first=False):
        self.light1 = random.randint(0, 1000)
        self.light2 = random.randint(0, 2000)
        self.value = [{"n": "light1", "v": self.light1, "u": "lx", "bt": time.time()},
                      {"n": "light2", "v": self.light2, "u": "lx"}]
        self.payload = (defines.Content_types["application/json"], json.dumps(self.value))
        if not self._coap_server.stopped.isSet():

            timer = threading.Timer(self.period, self.read_sensor)
            timer.setDaemon(True)
            timer.start()

            if not first and self._coap_server is not None:
                self._coap_server.notify(self)
                self.observe_count += 1


class CoAPServer(CoAP):
    def __init__(self, host, port, multicast=False):
        CoAP.__init__(self, (host, port), multicast)
        print "CoAP Server start on " + host + ":" + str(port)


def usage():  # pragma: no cover
    print "coapserver.py -i <ip address> -p <port>"


def main(argv):  # pragma: no cover
    ip = "0.0.0.0"
    port = 5683
    multicast = False
    try:
        opts, args = getopt.getopt(argv, "hi:p:m", ["ip=", "port=", "multicast"])
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
        elif opt in ("-m", "--multicast"):
            multicast = True

    server = CoAPServer(ip, port, multicast)
    power = PowerResource(coap_server=server)
    temperature = TemperatureResource(coap_server=server)
    battery = BatteryResource(coap_server=server)
    radio = RadioResource(coap_server=server)
    hum = HumidityResource(coap_server=server)
    light = LightResource(coap_server=server)
    server.add_resource('power/', power)
    server.add_resource('temperature/', temperature)
    server.add_resource('battery/', battery)
    server.add_resource('radio/', radio)
    server.add_resource('humidity/', hum)
    server.add_resource('light/', light)
    try:
        server.listen(10)
    except KeyboardInterrupt:
        print "Server Shutdown"
        server.close()
        print "Exiting..."


if __name__ == "__main__":  # pragma: no cover
    main(sys.argv[1:])
