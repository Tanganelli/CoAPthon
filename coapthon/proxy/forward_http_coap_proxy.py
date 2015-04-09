import os
from coapthon import defines
from coapthon.client.coap_protocol import HelperClient
from coapthon.messages.request import Request
from coapthon.serializer import Serializer
from twisted.application.service import Application
from twisted.python.log import ILogObserver, FileLogObserver
from twisted.python.logfile import DailyLogFile
from twisted.web.proxy import ProxyRequest, Proxy
from coapforwardproxy import CoAPForwardProxy
from twisted.internet import reactor
from twisted.web import proxy, http

__author__ = 'Giacomo Tanganelli'
__version__ = "2.0"

home = os.path.expanduser("~")
if not os.path.exists(home + "/.coapthon/"):
    os.makedirs(home + "/.coapthon/")

logfile = DailyLogFile("CoAPthon_http_forward_proxy.log", home + "/.coapthon/")
# Now add an observer that logs to a file
application = Application("CoAPthon_HTTP_Forward_Proxy")
application.setComponent(ILogObserver, FileLogObserver(logfile).emit)


# class HTTPCoAPResource(Resource):
#     def render_GET(self, request):
#         coap_uri = self.get_coap_uri(request)
#         request.setResponseCode(402)
#         return "<html><body>" + coap_uri + "</body></html>"
#
#     def get_coap_uri(self, request):
#         assert(isinstance(request, Request))
#         return request.uri
#
#
# class HTTPCoaPProxy(Site):
#     def __init__(self):
#         hc = Resource()
#         hc.putChild("hc", HTTPCoAPResource())
#         Site.__init__(self, hc)
#
#
# factory = HTTPCoaPProxy()
# reactor.listenTCP(8880, factory)
# reactor.run()


class HTTPCoaPProxyRequest(proxy.ProxyRequest):
    def __init__(self, channel, queued):
        ProxyRequest.__init__(self, channel, queued)
        self.coap_client = HelperClient(server=("127.0.0.1", 5683), forward=True)

    def process(self):
        coap_uri = self.get_coap_uri(self)
        print "Request from %s for %s" % (
            self.getClientIP(), coap_uri)

        if not coap_uri.startswith("coap://"):
            self.channel.transport.write(b"HTTP/1.1 400 Bad Request\r\n\r\n")
            return

        client_uri = self.parse_uri(coap_uri)
        if self.method == "GET" or self.method == "HEAD":
            function = self.coap_client.protocol.get
            args = (client_uri,)
            kwargs = {}
            callback = self.responseReceived
        elif self.method == "POST":
            function = self.coap_client.protocol.post
            args = (client_uri, self.args)
            kwargs = {}
            callback = self.responseReceived
        elif self.method == "PUT":
            function = self.coap_client.protocol.put
            args = (client_uri, self.args)
            kwargs = {}
            callback = self.responseReceived
        elif self.method == "DELETE":
            function = self.coap_client.protocol.delete
            args = (client_uri, )
            kwargs = {}
            callback = self.responseReceived
        else:
            self.channel.transport.write(b"HTTP/1.1 501 Not Implemented\r\n\r\n")
            return

        operations = [(function, args, kwargs, callback)]
        self.coap_client.start(operations)

    def requestReceived(self, command, path, version):
        ProxyRequest.requestReceived(self, command, path, version)

    def responseReceived(self, response):
        self.write(response.payload)
        self.finish()

    @staticmethod
    def get_coap_uri(request):
        assert(isinstance(request, ProxyRequest))
        ret = request.uri[4:]
        return ret

    @staticmethod
    def parse_uri(uri):
        t = uri.split("://")
        tmp = t[1]
        t = tmp.split("/")
        hostname = t[0]
        path = t[1]
        return path


class HTTPCoaPProxy(Proxy):
    requestFactory = HTTPCoaPProxyRequest

    # def allContentReceived(self):
    #     command = self._command
    #     path = self._path
    #     version = self._version
    #
    #     # reset ALL state variables, so we don't interfere with next request
    #     self.length = 0
    #     self._receivedHeaderCount = 0
    #     self.__first_line = 1
    #     self._transferDecoder = None
    #     del self._command, self._path, self._version
    #
    #     # Disable the idle timeout, in case this request takes a long
    #     # time to finish generating output.
    #     if self.timeOut:
    #         self._savedTimeOut = self.setTimeout(None)
    #
    #     req = self.requests[-1]
    #     print type(req)
    #     coap_uri = self.get_coap_uri(path)
    #     if not coap_uri.startswith("coap://"):
    #         self.transport.write(b"HTTP/1.1 400 Bad Request\r\n\r\n")
    #         self.transport.loseConnection()
    #         return
    #     client_uri = self.parse_uri(coap_uri)
    #     function = self.coap_client.protocol.get
    #     args = (client_uri,)
    #     kwargs = {}
    #     callback = self.response_received
    #
    #     operations = [(function, args, kwargs, callback)]
    #     self.coap_client.start(operations)




class HTTPCoaPProxyFactory(http.HTTPFactory):
    def buildProtocol(self, addr):
        return HTTPCoaPProxy()

reactor.listenTCP(8080, HTTPCoaPProxyFactory())
reactor.run()