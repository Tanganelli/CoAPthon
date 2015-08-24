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
        if expected.type is not None:
            self.assertEqual(message.type, expected.type)
        if expected.mid is not None:
            self.assertEqual(message.mid, expected.mid)

        self.assertEqual(message.code, expected.code)
        if expected.source is not None:
            self.assertEqual(message.source, source)
        if expected.token is not None:
            self.assertEqual(message.token, expected.token)
        if expected.payload is not None:
            self.assertEqual(message.payload, expected.payload)
        if expected.options is not None:
            self.assertEqual(message.options, expected.options)

        sock.close()

    def _test_plugtest_separate(self, message, expected, expected2):
        serializer = Serializer()
        datagram = serializer.serialize(message)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(datagram, message.destination)

        # expected

        datagram, source = sock.recvfrom(4096)
        host, port = source
        message = serializer.deserialize(datagram, host, port)
        if expected.type is not None:
            self.assertEqual(message.type, expected.type)
        if expected.mid is not None:
            self.assertEqual(message.mid, expected.mid)
        self.assertEqual(message.code, expected.code)
        if expected.source is not None:
            self.assertEqual(message.source, source)
        if expected.token is not None:
            self.assertEqual(message.token, expected.token)
        if expected.payload is not None:
            self.assertEqual(message.payload, expected.payload)
        if expected.options is not None:
            self.assertEqual(message.options, expected.options)

        # expected2

        datagram, source = sock.recvfrom(4096)
        host, port = source
        message = serializer.deserialize(datagram, host, port)
        if expected2.type is not None:
            self.assertEqual(message.type, expected2.type)
        if expected2.mid is not None:
            self.assertEqual(message.mid, expected2.mid)
        if expected2.code is not None:
            self.assertEqual(message.code, expected2.code)
        if expected2.source is not None:
            self.assertEqual(message.source, source)
        if expected2.token is not None:
            self.assertEqual(message.token, expected2.token)
        if expected2.payload is not None:
            self.assertEqual(message.payload, expected2.payload)
        if expected2.options is not None:
            self.assertEqual(message.options, expected2.options)

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

    def test_td_coap_core_03(self):
        print "TD_COAP_CORE_03"
        path = "/test"
        req = Request()

        req.code = defines.inv_codes['PUT']
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
        expected.code = defines.responses["CHANGED"]
        expected.token = None
        expected.payload = None

        self.current_mid += 1
        self._test_plugtest(req, expected)

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
        expected.payload = "<value>test</value>"
        option = Option()
        option.number = defines.inv_options["Content-Type"]
        option.value = defines.inv_content_types["application/xml"]
        expected.add_option(option)

        self.current_mid += 1
        self._test_plugtest(req, expected)

        req = Request()

        req.code = defines.inv_codes['GET']
        req.uri_path = path
        req.type = defines.inv_types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        option = Option()
        option.number = defines.inv_options["Accept"]
        option.value = defines.inv_content_types["application/xml"]
        req.add_option(option)

        expected = Response()
        expected.type = defines.inv_types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.responses["CONTENT"]
        expected.token = None
        expected.payload = "<value>test</value>"
        option = Option()
        option.number = defines.inv_options["Content-Type"]
        option.value = defines.inv_content_types["application/xml"]
        expected.add_option(option)

        self.current_mid += 1
        self._test_plugtest(req, expected)

    def test_td_coap_core_04(self):
        print "TD_COAP_CORE_04"
        path = "/test"
        req = Request()

        req.code = defines.inv_codes['DELETE']
        req.uri_path = path
        req.type = defines.inv_types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address

        expected = Response()
        expected.type = defines.inv_types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.responses["DELETED"]
        expected.token = None
        expected.payload = None

        self.current_mid += 1
        self._test_plugtest(req, expected)

    def test_td_coap_core_05(self):
        print "TD_COAP_CORE_05"
        path = "/test"
        req = Request()

        req.code = defines.inv_codes['GET']
        req.uri_path = path
        req.type = defines.inv_types["NON"]
        req._mid = self.current_mid
        req.destination = self.server_address

        expected = Response()
        expected.type = defines.inv_types["NON"]
        expected._mid = None
        expected.code = defines.responses["CONTENT"]
        expected.token = None
        expected.payload = "Test Resource"

        self.current_mid += 1
        self._test_plugtest(req, expected)

    def test_td_coap_core_06(self):
        print "TD_COAP_CORE_06"
        path = "/test_post"
        req = Request()

        req.code = defines.inv_codes['POST']
        req.uri_path = path
        req.type = defines.inv_types["NON"]
        o = Option()
        o.number = defines.inv_options["Content-Type"]
        o.value = defines.inv_content_types["application/xml"]
        req.add_option(o)
        req._mid = self.current_mid
        req.destination = self.server_address
        req.payload = "<value>test</value>"

        expected = Response()
        expected.type = defines.inv_types["NON"]
        expected._mid = None
        expected.code = defines.responses["CREATED"]
        expected.token = None
        expected.payload = None
        option = Option()
        option.number = defines.inv_options["Location-Path"]
        option.value = "/test_post"
        expected.add_option(option)

        self.current_mid += 1
        self._test_plugtest(req, expected)

    def test_td_coap_core_07(self):
        print "TD_COAP_CORE_07"
        path = "/test"
        req = Request()

        req.code = defines.inv_codes['PUT']
        req.uri_path = path
        req.type = defines.inv_types["NON"]
        o = Option()
        o.number = defines.inv_options["Content-Type"]
        o.value = defines.inv_content_types["application/xml"]
        req.add_option(o)
        req._mid = self.current_mid
        req.destination = self.server_address
        req.payload = "<value>test</value>"

        expected = Response()
        expected.type = defines.inv_types["NON"]
        expected._mid = None
        expected.code = defines.responses["CHANGED"]
        expected.token = None
        expected.payload = None

        self.current_mid += 1
        self._test_plugtest(req, expected)

    def test_td_coap_core_08(self):
        print "TD_COAP_CORE_08"
        path = "/test"
        req = Request()

        req.code = defines.inv_codes['DELETE']
        req.uri_path = path
        req.type = defines.inv_types["NON"]
        req._mid = self.current_mid
        req.destination = self.server_address

        expected = Response()
        expected.type = defines.inv_types["NON"]
        expected._mid = None
        expected.code = defines.responses["DELETED"]
        expected.token = None
        expected.payload = None

        self.current_mid += 1
        self._test_plugtest(req, expected)

    def test_td_coap_core_09(self):
        print "TD_COAP_CORE_09"
        path = "/separate"
        req = Request()

        req.code = defines.inv_codes['GET']
        req.uri_path = path
        req.type = defines.inv_types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address

        expected = Response()
        expected.type = defines.inv_types["ACK"]
        expected._mid = self.current_mid
        expected.code = None
        expected.token = None
        expected.payload = None

        expected2 = Response()
        expected2.type = defines.inv_types["CON"]
        expected2._mid = None
        expected2.code = defines.responses["CONTENT"]
        expected2.token = None
        expected2.payload = "Separate Resource"

        self.current_mid += 1
        self._test_plugtest_separate(req, expected, expected2)

    def test_td_coap_core_10(self):
        print "TD_COAP_CORE_10"
        path = "/test"
        req = Request()

        req.code = defines.inv_codes['GET']
        req.uri_path = path
        req.type = defines.inv_types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.token = "ciao"

        expected = Response()
        expected.type = defines.inv_types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.responses["CONTENT"]
        expected.token = None
        expected.payload = "Test Resource"
        expected.token = "ciao"

        self.current_mid += 1
        self._test_plugtest(req, expected)

    def test_td_coap_core_12(self):
        print "TD_COAP_CORE_12"
        path = "/seg1/seg2/seg3"
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
        expected.payload = "Test Resource"

        self.current_mid += 1
        self._test_plugtest(req, expected)

    def test_td_coap_core_13(self):
        print "TD_COAP_CORE_13"
        path = "/query?first=1&second=2&third=3"
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

if __name__ == '__main__':
    unittest.main()