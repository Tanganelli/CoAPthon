from Queue import Queue
import SocketServer
import socket
import sys
from coapthon2.layers.blockwise import Blockwise
from coapthon2.layers.connector import BaseCoAPRequestHandler
from coapthon2.layers.matcher import Matcher
from coapthon2.layers.observe import Observer
from coapthon2.layers.reliability import Reliability
from coapthon2.layers.token import Token

__author__ = 'Giacomo Tanganelli'
__version__ = "2.0"
__all__ = ["CoAPServer"]


class CoAPServer(SocketServer.UDPServer):
    def __init__(self, server_address, request_handler_class):
        SocketServer.UDPServer.__init__(self, server_address, request_handler_class)
        self._server_name = None
        self._server_port = None
        self.layer_stack = [Token(self), Observer(self), Blockwise(self), Reliability(self),
                            Matcher(self)]
        self.queue = Queue()

    def process(self):
        request = self.queue.get_nowait()
        i = len(self.layer_stack) - 2
        matcher = self.layer_stack[i]
        if not matcher.handle_request(request):
            pass
        i -= 1
        reliability = self.layer_stack[i]
        if not reliability.handle_request(request):
            pass
        i -= 1
        blockwise = self.layer_stack[i]
        if not blockwise.handle_request(request):
            pass
        i -= 1
        observe = self.layer_stack[i]
        if not observe.handle_request(request):
            pass
        i -= 1
        token = self.layer_stack[i]
        if not token.handle_request(request):
            pass
        i = len(self.layer_stack) - 1
        handler = self.layer_stack[i]
        handler.queue.put(request)

    def server_bind(self):
        """Override server_bind to store the server name."""
        SocketServer.UDPServer.server_bind(self)
        host, port = self.socket.getsockname()[:2]
        self._server_name = socket.getfqdn(host)
        self._server_port = port


def test(HandlerClass = BaseCoAPRequestHandler,
         ServerClass = CoAPServer):
    """Test the HTTP request handler class.

    This runs an HTTP server on port 8000 (or the first command line
    argument).

    """

    if sys.argv[1:]:
        port = int(sys.argv[1])
    else:
        port = 5683
    server_address = ('', port)

    httpd = ServerClass(server_address, HandlerClass)

    sa = httpd.socket.getsockname()
    print "Serving HTTP on", sa[0], "port", sa[1], "..."
    httpd.serve_forever()


if __name__ == '__main__':
    test()