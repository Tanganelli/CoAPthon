import random
import socket
import threading
import unittest
from coapserverPlugTest import CoAPServerPlugTest
from coapthon import defines
from coapthon.messages.option import Option
from coapthon.messages.request import Request
from coapthon.messages.response import Response
from coapthon.serializer import Serializer

__author__ = 'Giacomo Tanganelli'
__version__ = "2.0"


class Tests(unittest.TestCase):

    def setUp(self):
        self.server_address = ("127.0.0.1", 5683)
        self.current_mid = random.randint(1, 1000)
        self.server = CoAPServerPlugTest("127.0.0.1", 5683)
        self.server_thread = threading.Thread(target=self.server.listen, args=(10,))
        self.server_thread.start()

    def tearDown(self):
        self.server.close()
        self.server_thread.join(timeout=25)
        self.server = None

    def _test_plugtest(self, message, expected):
        serializer = Serializer()
        datagram = serializer.serialize(message)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(datagram, message.destination)

        datagram, source = sock.recvfrom(4096)
        host, port = source
        message = serializer.deserialize(datagram, host, port)

        print message
        self.assertEqual(message.type, expected.type)
        self.assertEqual(message.mid, expected.mid)
        self.assertEqual(message.code, expected.code)
        self.assertEqual(message.source, source)
        self.assertEqual(message.token, expected.token)
        self.assertEqual(message.payload, expected.payload)
        self.assertEqual(message.options, expected.options)

        sock.close()

    def test_td_coap_core_01(self):
        print "TD_COAP_CORE_01"
        path = "/test"
        req = Request()

        req.code = defines.inv_codes['GET']
        req.uri_path = path
        req.type = defines.inv_types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address

        expected = Response()
        expected.type = defines.inv_types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.responses["CONTENT"]
        expected.token = None
        expected.payload = "Test Resource"

        self.current_mid += 1
        self._test_plugtest(req, expected)

    def test_td_coap_core_02(self):
        print "TD_COAP_CORE_02"
        path = "/test_post"
        req = Request()

        req.code = defines.inv_codes['POST']
        req.uri_path = path
        req.type = defines.inv_types["CON"]
        o = Option()
        o.number = defines.inv_options["Content-Type"]
        o.value = defines.inv_content_types["application/xml"]
        req.add_option(o)
        req._mid = self.current_mid
        req.destination = self.server_address
        req.payload = "<value>test</value>"

        expected = Response()
        expected.type = defines.inv_types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.responses["CREATED"]
        expected.token = None
        expected.payload = None
        option = Option()
        option.number = defines.inv_options["Location-Path"]
        option.value = "/test_post"
        expected.add_option(option)

        self.current_mid += 1
        self._test_plugtest(req, expected)

if __name__ == '__main__':
    unittest.main()