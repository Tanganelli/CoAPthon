import re
import cherrypy
from jinja2 import Environment, FileSystemLoader

from coapthon import defines
from coapthon.client.helperclient import HelperClient
from coapthon.resource_directory.databaseManager import DatabaseManager

env = Environment(loader=FileSystemLoader('templates'))


class Root(object):
    def __init__(self):
        self._rd = (defines.RD_HOST, defines.RD_PORT)
        self._temperature_sensors = {}
        self._dbManager = DatabaseManager()
        self._clientPool = []
        self._responses = []
        self._read_rd()


    @staticmethod
    def _read_rd_sensor(client, path):
        response = client.get(path)
        link_format = response.payload
        sensors = []
        if response.payload is not None:
            while len(link_format) > 0:
                pattern = "<([^>]*)>;"
                result = re.match(pattern, link_format)
                if result is None:
                    break
                path = result.group(1)
                sensors.append(path)
                link_format = link_format[result.end(1) + 2:]
        return sensors

    def client_callback_observe(self, response):  # pragma: no cover
        self._responses.append(response.payload)

    def _read_rd(self):
        client = HelperClient(self._rd)
        path = 'rd-lookup/res?rt=temperature'
        self._temperature_sensors["temperature"] = self._read_rd_sensor(client, path)
        path = 'rd-lookup/res?rt=humidity'
        self._temperature_sensors["humidity"] = self._read_rd_sensor(client, path)
        path = 'rd-lookup/res?rt=light'
        self._temperature_sensors["light"] = self._read_rd_sensor(client, path)

        for k, lst_v in self._temperature_sensors.items():
            for v in lst_v:
                pattern = "coap://([0-9a-z.]*):([0-9]*)(/[a-zA-Z0-9/]*)"
                match = re.match(pattern=pattern, string=v)
                if match is not None:
                    host = match.group(1)
                    port = int(match.group(2))
                    path = match.group(3)
                    client_sensor = HelperClient((host, port))
                    client_sensor.observe(path, self.client_callback_observe)
                    self._clientPool.append(client_sensor)

    @cherrypy.expose
    def index(self):
        msg = self._responses.pop(0)
        return msg


if __name__ == '__main__':

    cherrypy.quickstart(Root(), '/')
