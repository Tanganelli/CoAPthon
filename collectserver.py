#!/usr/bin/env python

import getopt
import json
import random
import sys
import threading
import time
import serial

from coapthon import defines
from coapthon.client.helperclient import HelperClient
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
        self.cpu_power = random.uniform(0, 0.3)             # read_schema(self._coap_server, "cpu_power")
        self.lpm_power = random.uniform(0, 0.15)            # read_schema(self._coap_server, "lpm_power")
        self.listen_power = random.uniform(0, 0.4)          # read_schema(self._coap_server, "listen_power")
        self.transmit_power = random.uniform(0, 0.2)        # read_schema(self._coap_server, "transmit_power")
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
    def __init__(self, name="TemperatureResource", coap_server=None, parameter_name=None):
        super(TemperatureResource, self).__init__(name, coap_server, visible=True,
                                                  observable=True, allow_children=False)
        self.resource_type = "Temperature Resource"
        self.parameter_name = parameter_name
        self.content_type = "application/json"
        self.temperature = 0
        self.period = 5
        self.refresh_period = 30
        self.read_sensor(True)
        self.location_path = coap_server.register_rd_resource(self.resource_type, "temp")

        refresher = threading.Timer(self.refresh_period, coap_server.refresh_rd_resource, args=[coap_server,
                                                                                                self.refresh_period,
                                                                                                self.location_path])
        refresher.setDaemon(True)
        refresher.start()

        self.value = [{"n": "temperature", "v": self.temperature, "u": "Cel", "t": time.time()}]

    def render_GET(self, request):
        self.value = [{"n": "temperature", "v": self.temperature, "u": "Cel", "t": time.time()}]

        self.payload = (defines.Content_types["application/json"], json.dumps(self.value))
        return self

    def read_sensor(self, first=False):
        self.temperature = read_parameter_schema(self._coap_server, self.parameter_name)

        self.value = [{"n": "temperature", "v": self.temperature, "u": "Cel", "t": time.time()}]

        self.payload = (defines.Content_types["application/json"], json.dumps(self.value))
        if not self._coap_server.stopped.isSet():

            timer = threading.Timer(self.period, self.read_sensor)
            timer.setDaemon(True)
            timer.start()

            if not first and self._coap_server is not None:
                self._coap_server.notify(self)
                self.observe_count += 1

        print self.payload


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
        self.voltage = random.uniform(0, 5)         # read_schema(self._coap_server, "voltage")
        self.indicator = random.randint(1, 10)      # read_schema(self._coap_server, "indicator")

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
        self.rssi = random.uniform(-90, -10)            # read_schema(self._coap_server, "rssi")
        self.latency = random.uniform(0, 50)            # read_schema(self._coap_server, "latency")
        self.best_neighbor_id = "0"                     # read_schema(self._coap_server, "best_neighbor_id")
        self.best_neighbor_etx = random.randint(1, 10)  # read_schema(self._coap_server, "best_neighbor_etx")
        self.byte_sent = random.randint(1, 500)         # read_schema(self._coap_server, "byte_sent")
        self.byte_received = random.randint(1, 500)     # read_schema(self._coap_server, "byte_received")

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
    def __init__(self, name="HumidityResource", coap_server=None, parameter_name=None):
        super(HumidityResource, self).__init__(name, coap_server, visible=True,
                                               observable=True, allow_children=False)
        self.resource_type = "Humidity Resource"
        self.parameter_name = parameter_name
        self.content_type = "application/json"
        self.humidity = 0
        self.period = 5
        self.refresh_period = 30
        self.read_sensor(True)
        self.location_path = coap_server.register_rd_resource(self.resource_type, "hum")

        refresher = threading.Timer(self.refresh_period, coap_server.refresh_rd_resource, args=[coap_server,
                                                                                                self.refresh_period,
                                                                                                self.location_path])
        refresher.setDaemon(True)
        refresher.start()

        self.value = [{"n": "humidity", "v": self.humidity, "u": "%RH", "t": time.time()}]

    def render_GET(self, request):
        self.value = [{"n": "humidity", "v": self.humidity, "u": "%RH", "t": time.time()}]

        self.payload = (defines.Content_types["application/json"], json.dumps(self.value))
        return self

    def read_sensor(self, first=False):
        self.humidity = read_parameter_schema(self._coap_server, self.parameter_name)

        self.value = [{"n": "humidity", "v": self.humidity, "u": "%RH", "t": time.time()}]
        self.payload = (defines.Content_types["application/json"], json.dumps(self.value))
        if not self._coap_server.stopped.isSet():

            timer = threading.Timer(self.period, self.read_sensor)
            timer.setDaemon(True)
            timer.start()

            if not first and self._coap_server is not None:
                self._coap_server.notify(self)
                self.observe_count += 1

        print self.payload


class LightResource(Resource):
    def __init__(self, name="LightResource", coap_server=None, parameter_name=None):
        super(LightResource, self).__init__(name, coap_server, visible=True,
                                            observable=True, allow_children=False)
        self.resource_type = "Light Resource"
        self.parameter_name = parameter_name
        self.content_type = "application/json"
        self.light1 = 0
        self.light2 = 0
        self.period = 5
        self.refresh_period = 30
        self.read_sensor(True)
        self.location_path = coap_server.register_rd_resource(self.resource_type, "light")

        refresher = threading.Timer(self.refresh_period, coap_server.refresh_rd_resource, args=[coap_server,
                                                                                                self.refresh_period,
                                                                                                self.location_path])
        refresher.setDaemon(True)
        refresher.start()

        self.value = [{"n": "light1", "v": self.light1, "u": "lx", "bt": time.time()},
                      {"n": "light2", "v": self.light2, "u": "lx"}]

    def render_GET(self, request):
        self.value = [{"n": "light1", "v": self.light1, "u": "lx", "bt": time.time()},
                      {"n": "light2", "v": self.light2, "u": "lx"}]

        self.payload = (defines.Content_types["application/json"], json.dumps(self.value))
        return self

    def read_sensor(self, first=False):
        self.light1 = read_parameter_schema(self._coap_server, self.parameter_name + "1")
        self.light2 = read_parameter_schema(self._coap_server, self.parameter_name + "2")
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

        print self.payload


class CoAPServer(CoAP):
    def __init__(self, host, port, multicast=False):
        CoAP.__init__(self, (host, port), multicast)

        self.client = HelperClient(server=(host, 5684))      # RD parameter
        self.resource_schema = json.load(open(defines.RESOURCE_SCHEMA_PATH, "r"))
        self.parameter_schema = json.load(open(defines.SERIAL_PARAMETER_SCHEMA_PATH, "r"))
        self.parameter_schema_lock = threading.Lock()

        serial_listener = threading.Thread(target=self.serial_listen)
        serial_listener.setDaemon(True)
        serial_listener.start()

        self.rd_discovery()

        print "CoAP Server start on " + host + ":" + str(port)

    def serial_listen(self):
        port = serial.Serial(defines.SERIAL_PORT)
        port.baudrate = defines.SERIAL_BAUDRATE

        while True:
            try:
                received_parameter_dict = json.loads(port.readline())
            except ValueError:
                continue

            self.parameter_schema_lock.acquire()

            for key in self.parameter_schema:
                if key in received_parameter_dict:
                    value = received_parameter_dict[key]
                    typeof = self.parameter_schema[key]["parameter"]["type"]

                    if (typeof == "integer" and type(value) is int) or (typeof == "string" and type(value) is str):
                        self.parameter_schema[key]["parameter"]["value"] = value
                else:
                    self.parameter_schema[key]["parameter"]["value"] = -1  # error code

            self.parameter_schema_lock.release()

            print "schema parametri " + str(self.parameter_schema)

    def rd_discovery(self):
        # Test discover
        path = "/.well-known/core"
        response = self.client.get(path)
        print response.pretty_print()

    def register_rd_resource(self, resource_type, key):
        path = "rd?ep=node1"  # todo: node name from .json
        ct = {'content_type': defines.Content_types["application/link-format"]}
        payload = '</sensors/' + key + '>;ct=41;' + resource_type + ';if="sensor";'
        response = self.client.post(path, payload, None, None, **ct)
        print response.pretty_print()
        return response.location_path

    def refresh_rd_resource(self, coap_server, period, location_path):
        path = location_path
        response = self.client.post(path, '')
        print response.pretty_print()

        refresher = threading.Timer(period, coap_server.refresh_rd_resource, args=[coap_server, period, location_path])
        refresher.setDaemon(True)
        refresher.start()



def usage():  # pragma: no cover
    print "coapserver.py -i <ip address> -p <port>"


def read_parameter_schema(coap_server, key):
    coap_server.parameter_schema_lock.acquire()

    result = coap_server.parameter_schema[key]["parameter"]["value"]

    coap_server.parameter_schema_lock.release()

    if result is "":
        return -1
    return result


def main(argv):  # pragma: no cover
    ip = "127.0.0.1"  #0.0.0.0
    port = 5683  # 5683
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

    for key in server.resource_schema:
        classname = server.resource_schema[key]["className"]["classNameValue"]
        name = server.resource_schema[key]["name"]["nameValue"]

        resource = eval(classname + "(coap_server=server, parameter_name='" + name + "')")
        server.add_resource(name + '/', resource)

    try:
        server.listen(10)
    except KeyboardInterrupt:
        print "Server Shutdown"
        server.close()
        print "Exiting..."


if __name__ == "__main__":  # pragma: no cover
    main(sys.argv[1:])
