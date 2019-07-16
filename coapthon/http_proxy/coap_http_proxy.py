import argparse
import logging
import requests

from coapthon.defines import LOCALHOST, COAP_DEFAULT_PORT, DEFAULT_CH_PATH, Types, Codes, Content_types
from coapthon.forward_proxy.coap import CoAP
from coapthon.serializer import Serializer
from coapthon.messages.message import Message
from coapthon.messages.request import Request


__author__ = "Elias Grande"
__email__ = "e.grande@alumnos.urjc.es"

logger = logging.getLogger(__name__)

ch_path = DEFAULT_CH_PATH


""" the class that realizes the CoAP-HTTP/HTTPS Proxy """


class CHProxy:
    """
    This program implements a CoAP-HTTP/HTTPS Proxy.
    It is assumed that URI is formatted like this:
    coap://coap_ip:coap_port/coap2http
        Proxy-Uri: http://remote_ip:remote_port/resource
    You can run this program passing the parameters from the command line or you can use the CHProxy class in your own
    project.
    """
    def __init__(self, coap_ip=LOCALHOST, coap_port=COAP_DEFAULT_PORT, path=DEFAULT_CH_PATH):
        """
        Initialize the CH proxy.

        :param coap_ip: the ip of the ch_proxy server
        :param coap_port: the port of the ch_proxy server
        :param path: the path of the ch_proxy server
        
        """
        global ch_path
        ch_path = CHProxy.get_formatted_path(path)
        self.coap_ip = coap_ip
        self.coap_port = coap_port
        server_address = (self.coap_ip, self.coap_port)
        self.coap_server = CoAP_HTTP(server_address)

    def run(self):
        """
        Start the proxy.
        """
        logger.info('Starting CoAP-HTTP/HTTPS Proxy...')
        self.coap_server.listen(10)

    @staticmethod
    def get_formatted_path(path):
        """
        Uniform the path string

        :param path: the path
        :return: the uniform path
        """
        if path[0] != '/':
            path = '/' + path
        if path[-1] != '/':
            path = '{0}/'.format(path)
        return path


""" Overrides CoAP Forward Proxy """


class CoAP_HTTP(CoAP):

    def receive_datagram(self, args):
        """
        Handle messages coming from the udp socket.

        :param args: (data, client_address)
        """
        data, client_address = args

        logging.debug("receiving datagram")

        try:
            host, port = client_address
        except ValueError:
            host, port, tmp1, tmp2 = client_address

        client_address = (host, port)

        serializer = Serializer()
        message = serializer.deserialize(data, client_address)
        if isinstance(message, int):
            logger.error("receive_datagram - BAD REQUEST")
            rst = Message()
            rst.destination = client_address
            rst.type = Types["RST"]
            rst.code = message
            rst.mid = message.mid
            self.send_datagram(rst)
            return
        logger.debug("receive_datagram - " + str(message))

        if isinstance(message, Request):
            if not message.proxy_uri or message.uri_path != "coap2http":
                logger.error("receive_datagram - BAD REQUEST")
                rst = Message()
                rst.destination = client_address
                rst.type = Types["RST"]
                rst.code = Codes.BAD_REQUEST.number
                rst.mid = message.mid
                self.send_datagram(rst)
                return
            # Execute HTTP/HTTPS request
            http_response = CoAP_HTTP.execute_http_request(message.code, message.proxy_uri, message.payload)
            # HTTP response to CoAP response conversion
            coap_response = CoAP_HTTP.to_coap_response(http_response, message.code, client_address, message.mid)
            # Send datagram and return
            self.send_datagram(coap_response)
            return

        elif isinstance(message, Message):
            logger.error("Received message from %s", message.source)

        else:  # is Response
            logger.error("Received response from %s", message.source)

    @staticmethod
    def to_coap_response(http_response, request_method, client_address, mid):
        coap_msg = Message()
        coap_msg.destination = client_address
        coap_msg.type = Types["ACK"]
        coap_msg.code = CoAP_HTTP.to_coap_code(http_response.status_code, request_method)
        coap_msg.mid = mid
        if 'Content-Type' in http_response.headers:
            coap_msg.content_type = CoAP_HTTP.to_coap_content_type(http_response.headers['Content-Type'].split(";")[0])
        else:
            coap_msg.content_type = 0
        coap_msg.payload = http_response.content
        return coap_msg

    @staticmethod
    def to_coap_content_type(http_content_type):
        try:
            return Content_types[http_content_type]
        except:
            return 0

    @staticmethod
    def to_coap_code(http_code, request_method):
        # 4xx Client errors
        if http_code in [400, 405, 409, 414, 431]:
            return Codes.BAD_REQUEST.number
        elif http_code == 404:
            return Codes.NOT_FOUND.number
        elif http_code in [401, 403]:
            return Codes.FORBIDDEN.number
        elif http_code == 406:
            return Codes.NOT_ACCEPTABLE.number
        elif http_code == 412:
            return Codes.PRECONDITION_FAILED.number
        elif http_code == 413:
            return Codes.REQUEST_ENTITY_TOO_LARGE.number
        elif http_code == 415:
            return Codes.UNSUPPORTED_CONTENT_FORMAT.number
        # 5xx Server errors
        elif http_code == 500:
            return Codes.INTERNAL_SERVER_ERROR.number
        elif http_code == 501:
            return Codes.NOT_IMPLEMENTED.number
        elif http_code == 502:
            return Codes.BAD_GATEWAY.number
        elif http_code == 503:
            return Codes.SERVICE_UNAVAILABLE.number
        elif http_code == 504:
            return Codes.GATEWAY_TIMEOUT.number
        # 2xx Success
        elif http_code == 200 and Codes.GET.number:
            return Codes.CONTENT.number
        elif http_code == 201:
            return Codes.CREATED.number
        elif http_code == 204:
            if request_method == Codes.DELETE.number:
                return Codes.DELETED.number
            elif request_method in [Codes.PUT.number, Codes.POST.number]:
                return Codes.CHANGED.number
        # 3xx Redirection
        elif http_code == 304:
            return Codes.VALID.number
        # 1xx Informational response
        elif http_code == 100:
            return Codes.CONTINUE.number
        # ELSE
        return Codes.EMPTY.number

    @staticmethod
    def execute_http_request(method, uri, payload):
        response = None
        if method == Codes.GET.number:
            response = requests.get(url=uri)
        elif method == Codes.DELETE.number:
            response = requests.delete(url=uri)
        elif method == Codes.POST.number:
            response = requests.post(url=uri, data=payload)
        elif method == Codes.PUT.number:
            response = requests.put(url=uri, data=payload)
        return response


def get_command_line_args():
    parser = argparse.ArgumentParser(description='Run the CoAP-HTTP/HTTPS Proxy.')
    parser.add_argument('-ip', dest='coap_ip', default=LOCALHOST,
                        help='the ip of the ch_proxy server')
    parser.add_argument('-cp', dest='coap_port', default=COAP_DEFAULT_PORT,
                        help='the port of the ch_proxy server')
    parser.add_argument('-p', dest='path', default=DEFAULT_CH_PATH,
                        help='the path of the ch_proxy server')
    return parser.parse_args()


if __name__ == "__main__":
    args = get_command_line_args()
    ch_proxy = CHProxy(args.coap_ip, args.coap_port, args.path)
    ch_proxy.run()
