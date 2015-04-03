import random
import time
from twisted.test import proto_helpers
from twisted.trial import unittest
from coapserver import CoAPServer
from coapthon2 import defines
from coapthon2.messages.message import Message
from coapthon2.messages.option import Option
from coapthon2.messages.request import Request
from coapthon2.messages.response import Response
from coapthon2.serializer import Serializer

__author__ = 'Giacomo Tanganelli'
__version__ = "2.0"


class Tests(unittest.TestCase):

    def setUp(self):
        self.proto = CoAPServer("127.0.0.1", 5683)
        self.tr = proto_helpers.FakeDatagramTransport()
        self.proto.makeConnection(self.tr)
        self.current_mid = random.randint(1, 1000)

    def _test(self, message, expected):
        serializer = Serializer()
        datagram = serializer.serialize(message)
        self.proto.datagramReceived(datagram, ("127.0.0.1", 5600))
        datagram, source = self.tr.written[-1]
        host, port = source
        message = serializer.deserialize(datagram, host, port)
        self.assertEqual(message.type, expected.type)
        self.assertEqual(message.mid, expected.mid)
        self.assertEqual(message.code, expected.code)
        self.assertEqual(message.source, source)
        self.assertEqual(message.token, expected.token)
        self.assertEqual(message.payload, expected.payload)
        self.assertEqual(message.options, expected.options)

        self.tr.written = []

    def _test_modular(self, lst):
        serializer = Serializer()
        for t in lst:
            message, expected = t
            send_ack = False
            if message is not None:
                datagram = serializer.serialize(message)
                self.proto.datagramReceived(datagram, ("127.0.0.1", 5600))
            else:
                send_ack = True

            datagram, source = self.tr.written.pop(0)
            host, port = source
            message = serializer.deserialize(datagram, host, port)
            self.assertEqual(message.type, expected.type)
            if not send_ack:
                self.assertEqual(message.mid, expected.mid)
            self.assertEqual(message.code, expected.code)
            self.assertEqual(message.source, source)
            self.assertEqual(message.token, expected.token)
            self.assertEqual(message.payload, expected.payload)
            self.assertEqual(message.options, expected.options)
            if send_ack:
                message = Message.new_ack(message)
                datagram = serializer.serialize(message)
                self.proto.datagramReceived(datagram, ("127.0.0.1", 5600))

        self.tr.written = []

    def _test_separate(self, message, notification):
        serializer = Serializer()
        datagram = serializer.serialize(message)
        self.proto.datagramReceived(datagram, ("127.0.0.1", 5600))

        datagram, source = self.tr.written[0]
        host, port = source
        message = serializer.deserialize(datagram, host, port)

        self.assertEqual(message.type, defines.inv_types["ACK"])
        self.assertEqual(message.code, None)
        self.assertEqual(message.mid, self.current_mid + 4)
        self.assertEqual(message.source, source)

        datagram, source = self.tr.written[1]
        host, port = source
        message = serializer.deserialize(datagram, host, port)

        self.assertEqual(message.type, notification.type)
        self.assertEqual(message.code, notification.code)
        self.assertEqual(message.source, source)
        self.assertEqual(message.token, notification.token)
        self.assertEqual(message.payload, notification.payload)
        self.assertEqual(message.options, notification.options)

        self.tr.written = []

        message = Message.new_ack(message)
        datagram = serializer.serialize(message)
        self.proto.datagramReceived(datagram, ("127.0.0.1", 5600))
        self.tr.written = []

    def tearDown(self):
        self.proto.stopProtocol()
        del self.proto
        del self.tr

    def test_get_storage(self):
        args = ("/storage",)
        kwargs = {}
        path = args[0]
        req = Request()
        for key in kwargs:
            o = Option()
            o.number = defines.inv_options[key]
            o.value = kwargs[key]
            req.add_option(o)

        req.code = defines.inv_codes['GET']
        req.uri_path = path
        req.type = defines.inv_types["CON"]
        req.mid = self.current_mid

        expected = Response()
        expected.type = defines.inv_types["ACK"]
        expected.mid = self.current_mid
        expected.code = defines.responses["CONTENT"]
        expected.token = None
        expected.payload = "Storage Resource for PUT, POST and DELETE"

        self._test(req, expected)

    def test_get_not_found(self):
        args = ("/not_found",)
        kwargs = {}
        path = args[0]
        req = Request()
        for key in kwargs:
            o = Option()
            o.number = defines.inv_options[key]
            o.value = kwargs[key]
            req.add_option(o)

        req.code = defines.inv_codes['GET']
        req.uri_path = path
        req.type = defines.inv_types["CON"]
        req.mid = self.current_mid + 1

        expected = Response()
        expected.type = defines.inv_types["NON"]
        expected.mid = self.current_mid + 1
        expected.code = defines.responses["NOT_FOUND"]
        expected.token = None
        expected.payload = None

        self._test(req, expected)

    def test_post_and_get_storage(self):
        args = ("/storage/data1",)
        kwargs = {}
        path = args[0]
        req = Request()
        for key in kwargs:
            o = Option()
            o.number = defines.inv_options[key]
            o.value = kwargs[key]
            req.add_option(o)

        req.code = defines.inv_codes['POST']
        req.uri_path = path
        req.type = defines.inv_types["CON"]
        req.mid = self.current_mid + 2
        req.payload = "Created"

        expected = Response()
        expected.type = defines.inv_types["ACK"]
        expected.mid = self.current_mid + 2
        expected.code = defines.responses["CREATED"]
        expected.token = None
        expected.payload = None
        option = Option()
        option.number = defines.inv_options["Location-Path"]
        option.value = "storage/data1"
        expected.add_option(option)

        self._test(req, expected)

        req = Request()
        for key in kwargs:
            o = Option()
            o.number = defines.inv_options[key]
            o.value = kwargs[key]
            req.add_option(o)

        req.code = defines.inv_codes['GET']
        req.uri_path = path
        req.type = defines.inv_types["CON"]
        req.mid = self.current_mid + 3

        expected = Response()
        expected.type = defines.inv_types["ACK"]
        expected.mid = self.current_mid + 3
        expected.code = defines.responses["CONTENT"]
        expected.token = None
        expected.payload = "Created"

    def test_long(self):
        args = ("/long",)
        kwargs = {}
        path = args[0]
        req = Request()
        for key in kwargs:
            o = Option()
            o.number = defines.inv_options[key]
            o.value = kwargs[key]
            req.add_option(o)

        req.code = defines.inv_codes['GET']
        req.uri_path = path
        req.type = defines.inv_types["CON"]
        req.mid = self.current_mid

        expected = Response()
        expected.type = defines.inv_types["ACK"]
        expected.mid = self.current_mid
        expected.code = None
        expected.token = None
        expected.payload = None

        expected2 = Response()
        expected2.type = defines.inv_types["CON"]
        expected2.code = defines.responses["CONTENT"]
        expected2.token = None
        expected2.payload = "Long Time"

        self._test_modular([(req, expected), (None, expected2)])

    def test_big(self):
        args = ("/big",)
        path = args[0]

        req = Request()
        req.code = defines.inv_codes['GET']
        req.uri_path = path
        req.type = defines.inv_types["CON"]
        req.mid = self.current_mid

        expected = Response()
        expected.type = defines.inv_types["ACK"]
        expected.mid = self.current_mid
        expected.code = defines.responses["CONTENT"]
        expected.token = None
        expected.payload = None
        option = Option()
        option.number = defines.inv_options["BLOCK2"]
        option.value = 14
        expected.add_option(option)

        req2 = Request()
        req2.code = defines.inv_codes['GET']
        req2.uri_path = path
        req2.type = defines.inv_types["CON"]
        req2.mid = self.current_mid + 1
        option = Option()
        option.number = defines.inv_options["BLOCK2"]
        option.value = 22
        req2.add_option(option)

        expected2 = Response()
        expected2.type = defines.inv_types["CON"]
        expected2.code = defines.responses["CONTENT"]
        expected2.token = None
        expected2.payload = "Long Time"

        self._test_modular([(req, expected), (None, expected2)])

    def test_get_separate(self):
        args = ("/separate",)
        kwargs = {}
        path = args[0]
        req = Request()
        for key in kwargs:
            o = Option()
            o.number = defines.inv_options[key]
            o.value = kwargs[key]
            req.add_option(o)

        req.code = defines.inv_codes['GET']
        req.uri_path = path
        req.type = defines.inv_types["CON"]
        req.mid = self.current_mid + 4

        expected = Response()
        expected.type = defines.inv_types["CON"]
        expected.code = defines.responses["CONTENT"]
        expected.token = None
        expected.payload = "Separate"

        self._test_separate(req, expected)

    # def _test_notification(self, message, expected, req_put, expected_put, notification):
    #     serializer = Serializer()
    #     datagram = serializer.serialize(message)
    #     self.proto.datagramReceived(datagram, ("127.0.0.1", 5600))
    #     print self.tr.written
    #     datagram, source = self.tr.written[0]
    #     self.tr.written = []
    #     host, port = source
    #     message = serializer.deserialize(datagram, host, port)
    #     self.assertEqual(message.type, expected.type)
    #     self.assertEqual(message.mid, expected.mid)
    #     self.assertEqual(message.code, expected.code)
    #     self.assertEqual(message.source, source)
    #     self.assertEqual(message.token, expected.token)
    #     self.assertEqual(message.payload, expected.payload)
    #     self.assertEqual(message.options, expected.options)
    #
    #     datagram = serializer.serialize(req_put)
    #     self.proto.datagramReceived(datagram, ("127.0.0.1", 5600))
    #     print self.tr.written
    #     datagram, source = self.tr.written[0]
    #     self.tr.written = []
    #
    #     host, port = source
    #     message = serializer.deserialize(datagram, host, port)
    #     self.assertEqual(message.type, expected_put.type)
    #     self.assertEqual(message.mid, expected_put.mid)
    #     self.assertEqual(message.code, expected_put.code)
    #     self.assertEqual(message.source, source)
    #     self.assertEqual(message.token, expected_put.token)
    #     self.assertEqual(message.payload, expected_put.payload)
    #     self.assertEqual(message.options, expected_put.options)
    #     while True:
    #         try:
    #             datagram, source = self.tr.written[0]
    #             print message
    #             break
    #         except:
    #             continue
    #     while True:
    #         try:
    #             datagram, source = self.tr.written[1]
    #             print message
    #             break
    #         except:
    #             continue
    #     host, port = source
    #     message = serializer.deserialize(datagram, host, port)
    #
    #     self.assertEqual(message.type, notification.type)
    #     self.assertEqual(message.code, notification.code)
    #     self.assertEqual(message.source, source)
    #     self.assertEqual(message.token, notification.token)
    #     self.assertEqual(message.payload, notification.payload)
    #     self.assertEqual(message.options, notification.options)
    #
    #     self.tr.written = []
    #
    #     message = Message.new_ack(message)
    #     datagram = serializer.serialize(message)
    #     self.proto.datagramReceived(datagram, ("127.0.0.1", 5600))
    #
    #     self.tr.written = []

    # def test_observing(self):
    #     args = ("/basic",)
    #     path = args[0]
    #
    #     req = Request()
    #     req.code = defines.inv_codes['GET']
    #     req.uri_path = path
    #     req.type = defines.inv_types["CON"]
    #     req.mid = self.current_mid + 5
    #     o = Option()
    #     o.number = defines.inv_options["Observe"]
    #     o.value = 0
    #     req.add_option(o)
    #
    #     expected = Response()
    #     expected.type = defines.inv_types["ACK"]
    #     expected.mid = self.current_mid + 5
    #     expected.code = defines.responses["CONTENT"]
    #     expected.token = None
    #     expected.payload = "Basic Resource"
    #     option = Option()
    #     option.number = defines.inv_options["Observe"]
    #     option.value = 1
    #     expected.add_option(option)
    #
    #     req_put = Request()
    #     req_put.code = defines.inv_codes['PUT']
    #     req_put.uri_path = path
    #     req_put.type = defines.inv_types["CON"]
    #     req_put.mid = self.current_mid + 6
    #     req_put.payload = "Edited"
    #
    #     expected_put = Response()
    #     expected_put.type = defines.inv_types["ACK"]
    #     expected_put.mid = self.current_mid + 6
    #     expected_put.code = defines.responses["CHANGED"]
    #     expected_put.token = None
    #     expected_put.payload = None
    #
    #     notification = Response()
    #     notification.type = defines.inv_types["CON"]
    #     notification.code = defines.responses["CONTENT"]
    #     notification.token = None
    #     notification.payload = "Edited"
    #     option = Option()
    #     option.number = defines.inv_options["Observe"]
    #     option.value = 2
    #     notification.add_option(option)
    #
    #     self._test_modular([(req, expected), (req_put, expected_put), (None, notification)])

