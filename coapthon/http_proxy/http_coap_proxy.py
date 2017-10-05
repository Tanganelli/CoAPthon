import argparse
import logging

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from coapthon.client.helperclient import HelperClient
from coapthon.utils import parse_uri
from coapthon.defines import Codes, DEFAULT_HC_PATH, HC_PROXY_DEFAULT_PORT, COAP_DEFAULT_PORT, LOCALHOST, BAD_REQUEST, \
    NOT_IMPLEMENTED, CoAP_HTTP
from coapthon.defines import COAP_PREFACE
from urlparse import urlparse

__author__ = "Marco Ieni, Davide Foti"
__email__ = "marcoieni94@gmail.com, davidefoti.uni@gmail.com"

logger = logging.getLogger(__name__)

hc_path = DEFAULT_HC_PATH

""" the class that realizes the HTTP-CoAP Proxy """


class HCProxy:
    """
    This program implements an HTTP-CoAP Proxy without using external libraries.
    It is assumed that URI is formatted like this:
    http://hc_proxy_ip:proxy_port/hc/coap://server_coap_ip:server_coap_port/resource
    You can run this program passing the parameters from the command line or you can use the HCProxy class in your own
    project.
    """
    def __init__(self, path=DEFAULT_HC_PATH, hc_port=HC_PROXY_DEFAULT_PORT, ip=LOCALHOST,
                 coap_port=COAP_DEFAULT_PORT):
        """
        Initialize the HC proxy.

        :param path: the path of the hc_proxy server
        :param hc_port: the port of the hc_proxy server
        :param ip: the ip of the hc_proxy server
        :param coap_port: the coap server port you want to reach
        """
        global hc_path
        hc_path = HCProxy.get_formatted_path(path)
        self.hc_port = hc_port
        self.ip = ip
        self.coap_port = coap_port

    def run(self):
        """
        Start the proxy.
        """
        server_address = (self.ip, self.hc_port)
        hc_proxy = HTTPServer(server_address, HCProxyHandler)
        logger.info('Starting HTTP-CoAP Proxy...')
        hc_proxy.serve_forever()  # the server listen to http://ip:hc_port/path

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


class CoapUri:  # this class takes the URI from the HTTP URI
    """ Class that can manage and inbox the CoAP URI """
    def __init__(self, coap_uri):
        self.uri = coap_uri
        self.host, self.port, self.path = parse_uri(coap_uri)

    def get_uri_as_list(self):
        """
        Split the uri into <scheme>://<netloc>/<path>;<params>?<query>#<fragment>

        :return: the split uri
        """
        return urlparse(self.uri)

    def get_payload(self):
        """
        Return the query string of the uri.

        :return: the query string as a list
        """
        temp = self.get_uri_as_list()
        query_string = temp[4]
        if query_string == "":
            return None  # Bad request error code
        query_string_as_list = str.split(query_string, "=")
        return query_string_as_list[1]

    def __str__(self):
        return self.uri


class HCProxyHandler(BaseHTTPRequestHandler):
    """ It maps the requests from HTTP to CoAP """
    coap_uri = None
    client = None

    def set_coap_uri(self):
        """
        Create a CoAP Uri
        """
        self.coap_uri = CoapUri(self.path[len(hc_path):])

    def do_initial_operations(self):
        """
        Setup the client for interact with remote server
        """
        if not self.request_hc_path_corresponds():
            # the http URI of the request is not the same of the one specified by the admin for the hc proxy,
            # so I do not answer
            # For example the admin setup the http proxy URI like: "http://127.0.0.1:8080:/my_hc_path/" and the URI of
            # the requests asks for "http://127.0.0.1:8080:/another_hc_path/"
            return
        self.set_coap_uri()
        self.client = HelperClient(server=(self.coap_uri.host, self.coap_uri.port))

    def do_GET(self):
        """
        Perform a GET request
        """
        self.do_initial_operations()
        coap_response = self.client.get(self.coap_uri.path)
        self.client.stop()
        logger.info("Server response: %s", coap_response.pretty_print())
        self.set_http_response(coap_response)

    def do_HEAD(self):
        """
        Perform a HEAD request
        """
        self.do_initial_operations()
        # the HEAD method is not present in CoAP, so we treat it
        # like if it was a GET and then we exclude the body from the response
        # with send_body=False we say that we do not need the body, because it is a HEAD request
        coap_response = self.client.get(self.coap_uri.path)
        self.client.stop()
        logger.info("Server response: %s", coap_response.pretty_print())
        self.set_http_header(coap_response)

    def do_POST(self):
        """
        Perform a POST request
        """
        # Doesn't do anything with posted data
        # print "uri: ", self.client_address, self.path
        self.do_initial_operations()
        payload = self.coap_uri.get_payload()
        if payload is None:
            logger.error("BAD POST REQUEST")
            self.send_error(BAD_REQUEST)
            return
        coap_response = self.client.post(self.coap_uri.path, payload)
        self.client.stop()
        logger.info("Server response: %s", coap_response.pretty_print())
        self.set_http_response(coap_response)

    def do_PUT(self):
        """
        Perform a PUT request
        """
        self.do_initial_operations()
        payload = self.coap_uri.get_payload()
        if payload is None:
            logger.error("BAD PUT REQUEST")
            self.send_error(BAD_REQUEST)
            return
        logger.debug(payload)
        coap_response = self.client.put(self.coap_uri.path, payload)
        self.client.stop()
        logger.debug("Server response: %s", coap_response.pretty_print())
        self.set_http_response(coap_response)

    def do_DELETE(self):
        """
        Perform a DELETE request
        """
        self.do_initial_operations()
        coap_response = self.client.delete(self.coap_uri.path)
        self.client.stop()
        logger.debug("Server response: %s", coap_response.pretty_print())
        self.set_http_response(coap_response)

    def do_CONNECT(self):
        """
        Perform a CONNECT request. Reply with error, not implemented in CoAP
        """
        self.send_error(NOT_IMPLEMENTED)

    def do_OPTIONS(self):
        """
        Perform a OPTIONS request. Reply with error, not implemented in CoAP
        """
        self.send_error(NOT_IMPLEMENTED)

    def do_TRACE(self):
        """
        Perform a TRACE request. Reply with error, not implemented in CoAP
        """
        self.send_error(NOT_IMPLEMENTED)

    def request_hc_path_corresponds(self):
        """
        Tells if the hc path of the request corresponds to that specified by the admin

        :return: a boolean that says if it corresponds or not
        """
        uri_path = self.path.split(COAP_PREFACE)
        request_hc_path = uri_path[0]
        logger.debug("HCPATH: %s", hc_path)
        # print HC_PATH
        logger.debug("URI: %s", request_hc_path)
        if hc_path != request_hc_path:
            return False
        else:
            return True

    def set_http_header(self, coap_response):
        """
        Sets http headers.

        :param coap_response: the coap response
        """
        logger.debug(
                ("Server: %s\n"\
                        "codice risposta: %s\n"\
                        "PROXED: %s\n"\
                        "payload risposta: %s"),
                coap_response.source,
                coap_response.code,
                CoAP_HTTP[Codes.LIST[coap_response.code].name],
                coap_response.payload)
        self.send_response(int(CoAP_HTTP[Codes.LIST[coap_response.code].name]))
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def set_http_body(self, coap_response):
        """
        Set http body.

        :param coap_response: the coap response
        """
        if coap_response.payload is not None:
            body = "<html><body><h1>", coap_response.payload, "</h1></body></html>"
            self.wfile.write("".join(body))
        else:
            self.wfile.write("<html><body><h1>None</h1></body></html>")

    def set_http_response(self, coap_response):
        """
        Set http response.

        :param coap_response: the coap response
        """
        self.set_http_header(coap_response)
        self.set_http_body(coap_response)
        return


def get_command_line_args():
    parser = argparse.ArgumentParser(description='Run the HTTP-CoAP Proxy.')
    parser.add_argument('-p', dest='path', default=DEFAULT_HC_PATH,
                        help='the path of the hc_proxy server')
    parser.add_argument('-hp', dest='hc_port', default=HC_PROXY_DEFAULT_PORT,
                        help='the port of the hc_proxy server')
    parser.add_argument('-ip', dest='ip', default=LOCALHOST,
                        help='the ip of the hc_proxy server')
    parser.add_argument('-cp', dest='coap_port', default=COAP_DEFAULT_PORT,
                        help='the coap server port you want to reach')
    return parser.parse_args()


if __name__ == "__main__":
    args = get_command_line_args()
    hc_proxy = HCProxy(args.path, int(args.hc_port), args.ip, args.coap_port)
    hc_proxy.run()
