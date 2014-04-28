import socket
import SocketServer
import sys
from bitstring import BitStream

__author__ = 'Giacomo Tanganelli'
__version__ = "2.0"
__all__ = ["CoAPServer", "BaseCoAPRequestHandler"]


class CoAPServer(SocketServer.UDPServer):

    def __init__(self, server_address, request_handler_class):
        SocketServer.UDPServer.__init__(self, server_address, request_handler_class)
        self._server_name = None
        self._server_port = None

    def server_bind(self):
        """Override server_bind to store the server name."""
        SocketServer.UDPServer.server_bind(self)
        host, port = self.socket.getsockname()[:2]
        self._server_name = socket.getfqdn(host)
        self._server_port = port


class BaseCoAPRequestHandler(SocketServer.DatagramRequestHandler):
    # The Python system version, truncated to its first component.
    sys_version = "Python/" + sys.version.split()[0]

    # The server software version.  You may want to override this.
    # The format is multiple whitespace-separated strings,
    # where each string is of the form name[/version].
    server_version = "BaseCoAP/" + __version__

    def __init__(self, request, client_address, server):
        SocketServer.DatagramRequestHandler.__init__(self, request, client_address, server)
        self._reader = None

    def handle(self):
        try:
            buff = self.rfile.getvalue()
            self._reader = BitStream(bytes=buff)
        except socket.timeout, e:
            #a read or a write timed out.  Discard this connection
            self.log_error("Request timed out: %r", e)
            return