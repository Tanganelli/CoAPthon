# -*- coding: utf-8 -*-
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
        self.server_mid = random.randint(1000, 2000)
        self.server = CoAPServerPlugTest("127.0.0.1", 5683, starting_mid=self.server_mid)
        self.server_thread = threading.Thread(target=self.server.listen, args=(10,))
        self.server_thread.start()

    def tearDown(self):
        self.server.close()
        self.server_thread.join(timeout=25)
        self.server = None

    def _test_plugtest(self, message_list):
        serializer = Serializer()
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        for message, expected in message_list:
            if message is not None:
                datagram = serializer.serialize(message)
                sock.sendto(datagram, message.destination)
            if expected is not None:
                datagram, source = sock.recvfrom(4096)
                host, port = source
                received_message = serializer.deserialize(datagram, host, port)
                if expected.type is not None:
                    self.assertEqual(received_message.type, expected.type)
                if expected.mid is not None:
                    self.assertEqual(received_message.mid, expected.mid)
                self.assertEqual(received_message.code, expected.code)
                if expected.source is not None:
                    self.assertEqual(received_message.source, source)
                if expected.token is not None:
                    self.assertEqual(received_message.token, expected.token)
                if expected.payload is not None:
                    self.assertEqual(received_message.payload, expected.payload)
                if expected.options is not None:
                    self.assertEqual(received_message.options, expected.options)

        sock.close()

    # def test_td_coap_link_01(self):
    #     print "TD_COAP_LINK_01"
    #     path = "/.well-known/core"
    #     req = Request()
    #     req.code = defines.inv_codes['GET']
    #     req.uri_path = path
    #     req.type = defines.inv_types["CON"]
    #     req._mid = self.current_mid
    #     req.destination = self.server_address
    #
    #     expected = Response()
    #     expected.type = defines.inv_types["ACK"]
    #     expected._mid = self.current_mid
    #     expected.code = defines.responses["CONTENT"]
    #     expected.token = None
    #     option = Option()
    #     option.number = defines.inv_options["Content-Type"]
    #     option.value = defines.inv_content_types["application/link-format"]
    #     expected.add_option(option)
    #     expected.payload = """</separate>;</large-update>;</seg1/seg2/seg3>;rt="Type1",</large>;</seg1/seg2>;rt="Type1",</test>;rt="Type1",</obs>;</seg1>;rt="Type1",</query>;rt="Type1","""
    #
    #     self.current_mid += 1
    #     self._test_plugtest([(req, expected)])

    def test_td_coap_link_02(self):
        print "TD_COAP_LINK_02"
        path = "/.well-known/core"
        req = Request()
        req.code = defines.inv_codes['GET']
        req.uri_path = path
        req.type = defines.inv_types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.add_query("rt=Type1")

        expected = Response()
        expected.type = defines.inv_types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.responses["CONTENT"]
        expected.token = None
        option = Option()
        option.number = defines.inv_options["Content-Type"]
        option.value = defines.inv_content_types["application/link-format"]
        expected.add_option(option)
        expected.payload = """</seg1/seg2/seg3>;rt="Type1",</seg1/seg2>;rt="Type1",</test>;rt="Type1",</seg1>;rt="Type1",</query>;rt="Type1","""

        self.current_mid += 1
        self._test_plugtest([(req, expected)])

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
        self._test_plugtest([(req, expected)])

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
        self._test_plugtest([(req, expected)])

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
        exchange1 = (req, expected)

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
        exchange2 = (req, expected)

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
        exchange3 = (req, expected)
        self._test_plugtest([exchange1, exchange2, exchange3])

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
        self._test_plugtest([(req, expected)])

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
        self._test_plugtest([(req, expected)])

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
        self._test_plugtest([(req, expected)])

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
        self._test_plugtest([(req, expected)])

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
        self._test_plugtest([(req, expected)])

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
        expected2._mid = self.server_mid
        expected2.code = defines.responses["CONTENT"]
        expected2.token = None
        expected2.payload = "Separate Resource"

        self.current_mid += 1
        self._test_plugtest([(req, expected), (None, expected2)])

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
        self._test_plugtest([(req, expected)])

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
        self._test_plugtest([(req, expected)])

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
        self._test_plugtest([(req, expected)])

    def test_td_coap_obs_01(self):
        print "TD_COAP_OBS_01"
        path = "/obs"
        req = Request()

        req.code = defines.inv_codes['GET']
        req.uri_path = path
        req.type = defines.inv_types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.observe = 0

        expected = Response()
        expected.type = defines.inv_types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.responses["CONTENT"]
        expected.token = None
        expected.payload = "Observable Resource"
        expected.observe = 1

        expected2 = Response()
        expected2.type = defines.inv_types["CON"]
        expected2._mid = self.server_mid
        expected2.code = defines.responses["CONTENT"]
        expected2.token = None
        expected2.payload = "Observable Resource"
        expected2.observe = 2

        self.current_mid += 1
        self.server_mid += 1
        self._test_plugtest([(req, expected), (None, expected2)])

    def test_td_coap_obs_03(self):
        print "TD_COAP_OBS_03"
        path = "/obs"
        req = Request()

        req.code = defines.inv_codes['GET']
        req.uri_path = path
        req.type = defines.inv_types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.observe = 0

        expected = Response()
        expected.type = defines.inv_types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.responses["CONTENT"]
        expected.token = None
        expected.payload = "Observable Resource"
        expected.observe = 1

        self.current_mid += 1

        expected2 = Response()
        expected2.type = defines.inv_types["CON"]
        expected2._mid = self.server_mid
        expected2.code = defines.responses["CONTENT"]
        expected2.token = None
        expected2.payload = "Observable Resource"
        expected2.observe = 2

        rst = Response()
        rst.type = defines.inv_types["RST"]
        rst._mid = self.server_mid
        rst.code = defines.inv_codes["EMPTY"]
        rst.destination = self.server_address
        rst.token = None
        rst.payload = None

        self.current_mid += 1
        self.server_mid += 1
        self._test_plugtest([(req, expected), (None, expected2), (rst, None)])

    def test_td_coap_block_01(self):
        print "TD_COAP_BLOCK_01"
        path = "/large"

        req = Request()
        req.code = defines.inv_codes['GET']
        req.uri_path = path
        req.type = defines.inv_types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.add_block2(0, 0, 1024)

        expected = Response()
        expected.type = defines.inv_types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.responses["CONTENT"]
        expected.token = None
        expected.payload = None
        expected.block2 = (0, 1, 1024)

        exchange1 = (req, expected)
        self.current_mid += 1
        self.server_mid += 1

        req = Request()
        req.code = defines.inv_codes['GET']
        req.uri_path = path
        req.type = defines.inv_types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.add_block2(1, 0, 1024)

        expected = Response()
        expected.type = defines.inv_types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.responses["CONTENT"]
        expected.token = None
        expected.payload = None
        expected.block2 = (1, 0, 1024)

        exchange2 = (req, expected)
        self.current_mid += 1
        self.server_mid += 1

        self._test_plugtest([exchange1, exchange2])

    def test_td_coap_block_02(self):
        print "TD_COAP_BLOCK_02"
        path = "/large"

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
        expected.payload = None
        expected.block2 = (0, 1, 1024)

        exchange1 = (req, expected)
        self.current_mid += 1
        self.server_mid += 1

        req = Request()
        req.code = defines.inv_codes['GET']
        req.uri_path = path
        req.type = defines.inv_types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.add_block2(1, 0, 1024)

        expected = Response()
        expected.type = defines.inv_types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.responses["CONTENT"]
        expected.token = None
        expected.payload = None
        expected.block2 = (1, 0, 1024)

        exchange2 = (req, expected)
        self.current_mid += 1
        self.server_mid += 1

        self._test_plugtest([exchange1, exchange2])

    def test_td_coap_block_03(self):
        print "TD_COAP_BLOCK_03"
        path = "/large-update"

        req = Request()
        req.code = defines.inv_codes['PUT']
        req.uri_path = path
        req.type = defines.inv_types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.payload = """"Me sabbee plenty"—grunted Queequeg, puffing away at his pipe """
        req.block1 = (1, 1, 64)

        expected = Response()
        expected.type = defines.inv_types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.responses["CONTINUE"]
        expected.token = None
        expected.payload = None
        expected.block1 = (1, 1, 64)

        exchange1 = (req, expected)
        self.current_mid += 1
        self.server_mid += 1

        req = Request()
        req.code = defines.inv_codes['PUT']
        req.uri_path = path
        req.type = defines.inv_types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.payload = """and sitting up in bed. "You gettee in," he added, motioning"""
        req.block1 = (2, 0, 64)

        expected = Response()
        expected.type = defines.inv_types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.responses["CHANGED"]
        expected.token = None
        expected.payload = None

        exchange2 = (req, expected)
        self.current_mid += 1
        self.server_mid += 1

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
        expected.payload = """"Me sabbee plenty"—grunted Queequeg, puffing away at his pipe and sitting up in bed. "You gettee in," he added, motioning"""

        exchange3 = (req, expected)
        self.current_mid += 1

        self._test_plugtest([exchange1, exchange2, exchange3])

if __name__ == '__main__':
    unittest.main()
