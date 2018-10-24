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
    def __init__(self, name="TemperatureResource", coap_server=None, resource_key=None, subresources_keys=None):
        super(TemperatureResource, self).__init__(name, coap_server, visible=True,
                                                  observable=True, allow_children=False)
        self.resource_type = "temperature"
        self.resource_key = resource_key
        self.subresources_keys = subresources_keys
        self.content_type = "application/json"
        self.temperature = 0
        self.period = 5
        self.RD_registered = False
        self.location_path = ""
        self.read_sensor(True)
        self.value = [{"n": "temperature", "v": self.temperature, "u": "Cel", "t": time.time()}]

    def render_GET(self, request):
        self.value = [{"n": "temperature", "v": self.temperature, "u": "Cel", "t": time.time()}]

        self.payload = (defines.Content_types["application/json"], json.dumps(self.value))
        return self

    def read_sensor(self, first=False):
        self.temperature = read_parameter_schema(self._coap_server, self.resource_key, self.subresources_keys[0])
        self.value = [{"n": "temperature", "v": self.temperature, "u": "Cel", "t": time.time()}]
        self.payload = (defines.Content_types["application/json"], json.dumps(self.value))

        if self.temperature != -1:
            if self.RD_registered is False:
                self.location_path = self._coap_server.register_rd_resource(self.resource_type, self.resource_key)
                self.RD_registered = True
            else:
                self._coap_server.refresh_rd_resource(self.location_path)

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
        self.resource_type = "battery"
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
    def __init__(self, name="RadioResource", coap_server=None, parameter_name=None):
        super(RadioResource, self).__init__(name, coap_server, visible=True,
                                            observable=True, allow_children=False)
        self.resource_type = "radio"
        self.parameter_name = parameter_name
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
    def __init__(self, name="HumidityResource", coap_server=None, resource_key=None, subresources_keys=list):
        super(HumidityResource, self).__init__(name, coap_server, visible=True,
                                               observable=True, allow_children=False)
        self.resource_type = "humidity"
        self.resource_key = resource_key
        self.subresources_keys = subresources_keys
        self.content_type = "application/json"
        self.humidity = 0
        self.period = 5
        self.RD_registered = False
        self.location_path = ""
        self.read_sensor(True)
        self.value = [{"n": "humidity", "v": self.humidity, "u": "%RH", "t": time.time()}]

    def render_GET(self, request):
        self.value = [{"n": "humidity", "v": self.humidity, "u": "%RH", "t": time.time()}]

        self.payload = (defines.Content_types["application/json"], json.dumps(self.value))
        return self

    def read_sensor(self, first=False):
        self.humidity = read_parameter_schema(self._coap_server, self.resource_key, self.subresources_keys[0])
        self.value = [{"n": "humidity", "v": self.humidity, "u": "%RH", "t": time.time()}]
        self.payload = (defines.Content_types["application/json"], json.dumps(self.value))

        if self.humidity != -1:
            if self.RD_registered is False:
                self.location_path = self._coap_server.register_rd_resource(self.resource_type, self.resource_key)
                self.RD_registered = True
            else:
                self._coap_server.refresh_rd_resource(self.location_path)

        if not self._coap_server.stopped.isSet():

            timer = threading.Timer(self.period, self.read_sensor)
            timer.setDaemon(True)
            timer.start()

            if not first and self._coap_server is not None:
                self._coap_server.notify(self)
                self.observe_count += 1


class LightResource(Resource):
    def __init__(self, name="LightResource", coap_server=None, resource_key=None, subresources_keys=None):
        super(LightResource, self).__init__(name, coap_server, visible=True,
                                            observable=True, allow_children=False)
        self.resource_type = "light"
        self.resource_key = resource_key
        self.subresources_keys = subresources_keys
        self.content_type = "application/json"
        self.light1 = 0
        self.light2 = 0
        self.period = 5
        self.RD_registered = False
        self._registration_to_rd_thread = threading.Thread(target=self._registration_to_rd)
        self._registration_to_rd_thread.daemon = True
        self. _registration_to_rd_thread.start()
        self.location_path = ""
        self.read_sensor(True)
        self.value = [{"n": "light1", "v": self.light1, "u": "lx", "bt": time.time()},
                      {"n": "light2", "v": self.light2, "u": "lx", "bt": time.time()}]

    def _registration_to_rd(self):
        while True:
            if self.RD_registered is False:
                self.location_path = self._coap_server.register_rd_resource(self.resource_type, self.resource_key)
                self.RD_registered = True
            else:
                self._coap_server.refresh_rd_resource(self.location_path)
            time.sleep(60)

    def render_GET(self, request):
        self.value = [{"n": "light1", "v": self.light1, "u": "lx", "bt": time.time()},
                      {"n": "light2", "v": self.light2, "u": "lx", "bt": time.time()}]

        self.payload = (defines.Content_types["application/json"], json.dumps(self.value))
        return self

    def read_sensor(self, first=False):
        self.light1 = read_parameter_schema(self._coap_server, self.resource_key, self.subresources_keys[0])
        self.light2 = read_parameter_schema(self._coap_server, self.resource_key, self.subresources_keys[1])
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

        self.client = HelperClient(server=(defines.RD_HOST, defines.RD_PORT))
        self.node_resource_schema = json.load(open(defines.NODE_RESOURCE_SCHEMA_PATH, "r"))
        self.node_name = self.node_resource_schema["node"]["name"]["value"]

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
                subresources = self.parameter_schema[key]
                for subkey in subresources:
                    if subkey in received_parameter_dict:
                        value = received_parameter_dict[subkey]
                        typeof = subresources[subkey]["parameter"]["type"]

                        if (typeof == "integer" and type(value) is int) or (typeof == "string" and type(value) is str):
                            subresources[subkey]["parameter"]["value"] = value
                    else:
                        subresources[subkey]["parameter"]["value"] = -1  # error code

            self.parameter_schema_lock.release()
            print "schema parametri " + str(self.parameter_schema)

    def rd_discovery(self):
        # Test discover
        path = "/.well-known/core"
        response = self.client.get(path)
        print response.pretty_print()

    def register_rd_resource(self, resource_type, key):
        path = "rd?ep=" + self.node_name + "&con=coap://" + str(self.server_address[0]) + ":" + str(self.server_address[1])
        ct = {'content_type': defines.Content_types["application/link-format"]}
        payload = '</' + key + '>;ct=41;' + resource_type + ';if="sensor";'
        response = self.client.post(path, payload, None, None, **ct)
        print response.pretty_print()
        return response.location_path

    def refresh_rd_resource(self, location_path):
        path = location_path
        response = self.client.post(path, '')
        print response.pretty_print()


def usage():  # pragma: no cover
    print "coapserver.py -i <ip address> -p <port>"


def read_parameter_schema(coap_server, key, subresource):
    coap_server.parameter_schema_lock.acquire()

    result = coap_server.parameter_schema[key][subresource]["parameter"]["value"]

    coap_server.parameter_schema_lock.release()

    return result


def main(argv):  # pragma: no cover
    ip = "127.0.0.1"
    port = 5681
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

    resources = server.node_resource_schema["node"]["resources"]
    for key in resources:
        class_name = resources[key]["className"]["value"]
        resource_key = resources[key]["resourceKey"]["value"]
        subresources_keys = resources[key]["subresources"]["items"]

        resource = eval(class_name + "(coap_server=server, resource_key='" + resource_key +
                        "', subresources_keys=subres_key)", {"__builtins__": globals()},
                        {"subres_key": subresources_keys, "server": server})

        server.add_resource(resource_key + '/', resource)

    try:
        server.listen(10)
    except KeyboardInterrupt:
        print "Server Shutdown"
        server.close()
        print "Exiting..."


if __name__ == "__main__":  # pragma: no cover
    main(sys.argv[1:])
