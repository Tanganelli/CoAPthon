import SocketServer
import socket
import sys
from coapthon2.layers.connector import BaseCoAPRequestHandler
from coapthon2.layers.layer import Layer

__author__ = 'Giacomo Tanganelli'
__version__ = "2.0"
__all__ = ["CoAPServer"]


class CoAPServer(SocketServer.UDPServer):
    def __init__(self, server_address, request_handler_class):
        SocketServer.UDPServer.__init__(self, server_address, request_handler_class)
        self._server_name = None
        self._server_port = None
        self.layer_stack = Layer()

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