from Queue import Queue
import socket
import SocketServer
import sys
from bitstring import BitStream, ReadError
from coapthon2 import defines
from coapthon2.messages.message import Message
from coapthon2.messages.option import Option
from coapthon2.messages.request import Request

__author__ = 'Giacomo Tanganelli'
__version__ = "2.0"
__all__ = ["BaseCoAPRequestHandler"]


class BaseCoAPRequestHandler(SocketServer.DatagramRequestHandler):
    # The Python system version, truncated to its first component.
    sys_version = "Python/" + sys.version.split()[0]

    # The server software version.  You may want to override this.
    # The format is multiple whitespace-separated strings,
    # where each string is of the form name[/version].
    server_version = "BaseCoAP/" + __version__

    def __init__(self, request, client_address, server):
        SocketServer.DatagramRequestHandler.__init__(self, request, client_address, server)
        ## The reader.
        self._reader = None
        self.command = None
        self.path = None
        self.queue = Queue()

    def send(self, message):
        self.serialize(message)
        self.wfile.flush()  # actually send the response 
        pass

    def handle(self):
        try:
            message = self.parse_message()
            if message is None:
                self.log_error("Message is not correct")
            elif isinstance(message, Request):
                self.server.layer_stack.append(self)
                self.server.queue.put(message)
                self.server.process()
                response = self.queue.get()
                self.wfile.flush()  # actually send the response if not already done.
            else:  # empty message
                pass
        except socket.timeout, e:
            #a read or a write timed out.  Discard this connection
            self.log_error("Request timed out: %r", e)
            return

    def parse_message(self):
        buff = self.rfile.getvalue()
        self._reader = BitStream(bytes=buff, length=(len(buff) * 8))
        version = self._reader.read(defines.VERSION_BITS).uint
        message_type = self._reader.read(defines.TYPE_BITS).uint
        token_length = self._reader.read(defines.TOKEN_LENGTH_BITS).uint
        code = self._reader.read(defines.CODE_BITS).uint
        mid = self._reader.read(defines.MESSAGE_ID_BITS).uint
        if self.is_response(code):
            self.send_error(406)
            return
        elif self.is_request(code):
            message = Request()
            message.code = code
        else:
            message = Message()
        message.source = self.client_address
        message.destination = self.server.server_address
        message.version = version
        message.type = message_type
        message.mid = mid

        if token_length > 0:
            message.token = self._reader.read(token_length * 8).bytes
        else:
            message.token = None

        current_option = 0
        try:
            while self._reader.pos < self._reader.len:
                next_byte = self._reader.peek(8).uint
                if next_byte != int(defines.PAYLOAD_MARKER):
                    # the first 4 bits of the byte represent the option delta
                    delta = self._reader.read(4).uint
                    current_option += self.read_option_value_from_nibble(delta)
                    # the second 4 bits represent the option length
                    length = self._reader.read(4).uint
                    option_length = self.read_option_value_from_nibble(length)

                    # read option
                    option_name, option_type, option_repeatable = defines.options[current_option]
                    if option_length == 0:
                        value = None
                    elif option_type == defines.INTEGER:
                        value = self._reader.read(option_length * 8).uint
                    else:
                        value = self._reader.read(option_length * 8).bytes

                    option = Option()
                    option.number = current_option
                    option.value = value

                    message.add_option(option)
                else:
                    self._reader.pos += 8  # skip payload marker
                    if self._reader.len <= self._reader.pos:
                        self.send_error(0)
                        raise ValueError("Payload Marker with no payload")
                    to_end = self._reader.len - self._reader.pos
                    message.payload = self._reader.read(to_end).bytes
            return message
        except ReadError, e:
            self.send_error(0)
            self.log_error("Error parsing message: %r", e)
        return None

    @staticmethod
    def is_request(code):
        """
        Checks if is request.

        @return: true, if is request
        """
        return defines.REQUEST_CODE_LOWER_BOUND <= code <= defines.REQUEST_CODE_UPPER_BOUNT

    @staticmethod
    def is_response(code):
        """
        Checks if is response.

        @return: true, if is response
        """
        return defines.RESPONSE_CODE_LOWER_BOUND <= code <= defines.RESPONSE_CODE_UPPER_BOUND

    @staticmethod
    def is_empty(code):
        """
        Checks if is empty.

        @return: true, if is empty
        """
        return code == defines.EMPTY_CODE

    def log_error(self, fmt, *args):
        raise NotImplemented

    def send_error(self, code, message=None):
        raise NotImplemented

    def read_option_value_from_nibble(self, nibble):
        """
        Calculates the value used in the extended option fields as specified in
        draft-ietf-core-coap-14, section 3.1

        @param nibble: the 4-bit option header value.
        @return: the value calculated from the nibble and the extended option value.
        """
        if nibble <= 12:
            return nibble
        elif nibble == 13:
            #self._reader.pos += 4
            tmp = self._reader.read(8).uint + 13
            #self._reader.pos -= 12
            return tmp
        elif nibble == 14:
            return self._reader.read(16).uint + 269
        else:
            raise ValueError("Unsupported option nibble " + nibble)

    def handle_request(self, message):

        self.command = defines.codes[message.code]
        mname = 'do_' + self.command
        if not hasattr(self, mname):
            self.send_error(501, "Unsupported method (%r)" % self.command)
            return
        method = getattr(self, mname)
        method()

    def do_GET(self):
        print("Handle GET")

    def serialize(self, message):
        pass

