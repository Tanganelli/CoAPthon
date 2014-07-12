import re
from coapthon2.messages.message import Message
from coapthon2.messages.response import Response
from coapthon2.serializer import Serializer
from coapthon2.utils import Tree
from twisted.python import log
from coapthon2 import defines
from coapthon2.client.coap_protocol import HelperClient
from coapthon2.messages.request import Request
from twisted.application.service import Application
from twisted.python.log import ILogObserver, FileLogObserver
from twisted.python.logfile import DailyLogFile
from coapthon2.proxy.forward_coap_protocol import ProxyCoAP
import xml.etree.ElementTree as ElementTree
from coapthon2.resources.resource import Resource

__author__ = 'Giacomo Tanganelli'
__version__ = "2.0"

from os.path import expanduser

home = expanduser("~")

logfile = DailyLogFile("CoAPthon_reverse_proxy.log", home + "/.coapthon/")
# Now add an observer that logs to a file
application = Application("CoAPthon_Reverse_Proxy")
application.setComponent(ILogObserver, FileLogObserver(logfile).emit)


class ReverseProxyCoAP(ProxyCoAP):
    def __init__(self, file_xml):
        ProxyCoAP.__init__(self)
        self._mapping = {}
        root = Resource('root', visible=False, observable=False, allow_children=True)
        root.path = '/'
        self.root = Tree(root)
        self.file_xml = file_xml

    def parse_config(self):
        tree = ElementTree.parse(self.file_xml)
        root = tree.getroot()
        for server in root.findall('server'):
            destination = server.text
            self.discover_remote(destination)

    @staticmethod
    def parse_core_link_format(link_format, root):
        while len(link_format) > 0:
            pattern = "<([^>]*)>;"
            result = re.match(pattern, link_format)
            path = result.group(1)
            path = path.split("/")
            path = path[1:]
            link_format = link_format[result.end(1) + 2:]
            pattern = "([^<,])*"
            result = re.match(pattern, link_format)
            attributes = result.group(0)
            dict_att = {}
            if len(attributes) > 0:
                attributes = attributes.split(";")
                for att in attributes:
                    a = att.split("=")
                    # TODO check correctness
                    dict_att[a[0]] = a[1]
                link_format = link_format[result.end(0) + 1:]

            while True:
                last, p = root.find_complete_last(path)
                if p is not None:
                    resource = Resource("/".join(path))
                    resource.path = p
                    if p == "".join(path):
                        resource.attributes = dict_att
                    last.add_child(resource)
                else:
                    break
        log.msg(root.dump())
        return root

    def discover_remote(self, destination):
        request = Request()
        assert (isinstance(destination, str))
        split = destination.split(":", 1)
        host = split[0]
        port = int(split[1])
        server = (host, port)
        request.destination = (host, port)
        request.type = defines.inv_types["CON"]
        request.mid = (self._currentMID + 1) % (1 << 16)
        request.code = defines.inv_codes["GET"]
        uri = "/" + defines.DISCOVERY_URL
        request.proxy_uri = uri
        client = HelperClient(server, True)
        token = self.generate_token()
        function = client.protocol.get
        args = (uri,)
        kwargs = {"Token": str(token)}
        callback = self.discover_remote_results
        err_callback = self.discover_remote_error
        operations = [(function, args, kwargs, (callback, err_callback))]
        key = hash(str(host) + str(port) + str(token))
        self._forward[key] = request
        key = hash(str(host) + str(port) + str((client.starting_mid + 1) % (1 << 16)))
        self._forward_mid[key] = request
        client.start(operations)

    def discover_remote_results(self, response):
        host, port = response.source
        key = hash(str(host) + str(port) + str(response.token))
        request = self._forward.get(key)
        if request is not None:
            del self._forward[key]
            host, port = response.source
            key = hash(str(host) + str(port) + str(response.mid))
            try:
                del self._forward_mid[key]
            except KeyError:
                log.err("MID has not been deleted")
            if response.code == defines.responses["CONTENT"]:
                resource = Resource('server', visible=True, observable=False, allow_children=True)
                resource.path = str(host) + ":" + str(port)
                resource = self.root.add_child(resource)
                self._mapping[str(host) + str(port)] = self.parse_core_link_format(response.payload, resource)
            else:
                log.err("Server: " + response.source + " isn't valid.")

    def discover_remote_error(self, mid, host, port):
        """
        Handler of errors. Send an error message to the client.

        :param mid: the mid of the response that generates the error.
        :param host: the host of the server.
        :param port: the port of the server.
        """
        key = hash(str(host) + str(port) + str(mid))
        request = self._forward_mid.get(key)
        if request is not None:
            del self._forward[key]
            key = hash(str(host) + str(port) + str(mid))
            try:
                del self._forward_mid[key]
            except KeyError:
                log.err("MID has not been deleted")
            log.err("Server: " + str(host) + ":" + str(port) + " isn't valid.")

    def datagramReceived(self, data, (host, port)):
        """
        Handler for received dUDP datagram.

        :param data: the UDP datagram
        :param host: source host
        :param port: source port
        """
        log.msg("Datagram received from " + str(host) + ":" + str(port))
        serializer = Serializer()
        message = serializer.deserialize(data, host, port)
        print "Message received from " + host + ":" + str(port)
        print "----------------------------------------"
        print message
        print "----------------------------------------"
        if isinstance(message, Request):
            log.msg("Received request")
            message = self.map(message)
            if message is not None:
                ret = self._request_layer.handle_request(message)
                if isinstance(ret, Request):
                    self.forward_request(ret)
                else:
                    return
        elif isinstance(message, Response):
            log.err("Received response")
            rst = Message.new_rst(message)
            rst = self._message_layer.matcher_response(rst)
            log.msg("Send RST")
            self.send(rst, host, port)
        elif isinstance(message, tuple):
            message, error = message
            response = Response()
            response.destination = (host, port)
            response.code = defines.responses[error]
            response = self.reliability_response(message, response)
            response = self._message_layer.matcher_response(response)
            log.msg("Send Error")
            self.send(response, host, port)
        elif message is not None:
            # ACK or RST
            log.msg("Received ACK or RST")
            self._message_layer.handle_message(message)

    def map(self, request):
        path = request.uri_path
        if request.uri_path == defines.DISCOVERY_URL:
            response = Response()
            response.destination = request.source
            response = self._resource_layer.discover(request, response)
            self.result_forward(response, request)
        server = self.root.find_complete(path)
        if server is not None:
            new_request = Request()
            segments = server.find_path().split("/")
            path = segments[2:]
            path = "/".join(path)
            segments = segments[1].split(":")
            host = segments[0]
            port = int(segments[1])
            #new_request.destination = (host, port)
            new_request.source = request.source
            new_request.type = request.type
            new_request.mid = (self._currentMID + 1) % (1 << 16)
            new_request.code = request.code
            new_request.proxy_uri = "coap://" + str(host) + ":" + str(port) + "/" + path
            new_request.payload = request.payload
            for option in request.options:
                if option.name == defines.inv_options["Uri-Path"]:
                    continue
                if option.name == defines.inv_options["Uri-Query"]:
                    continue
                if option.name == defines.inv_options["Uri-Host"]:
                    continue
                new_request.add_option(option)
            return new_request
        return None

