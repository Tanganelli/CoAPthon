import random
from threading import Thread
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
        self.proto.datagramReceived(datagram, ("127.0.0.1", 5683))
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

    def _test_notification(self, message, expected, req_put, expected_put, notification):
        serializer = Serializer()
        datagram = serializer.serialize(message)
        self.proto.datagramReceived(datagram, ("127.0.0.1", 5600))
        print self.tr.written
        datagram, source = self.tr.written[0]
        host, port = source
        message = serializer.deserialize(datagram, host, port)
        self.assertEqual(message.type, expected.type)
        self.assertEqual(message.mid, expected.mid)
        self.assertEqual(message.code, expected.code)
        self.assertEqual(message.source, source)
        self.assertEqual(message.token, expected.token)
        self.assertEqual(message.payload, expected.payload)
        self.assertEqual(message.options, expected.options)

        datagram = serializer.serialize(req_put)
        self.proto.datagramReceived(datagram, ("127.0.0.1", 5600))
        datagram, source = self.tr.written[1]
        print self.tr.written
        host, port = source
        message = serializer.deserialize(datagram, host, port)
        self.assertEqual(message.type, expected_put.type)
        self.assertEqual(message.mid, expected_put.mid)
        self.assertEqual(message.code, expected_put.code)
        self.assertEqual(message.source, source)
        self.assertEqual(message.token, expected_put.token)
        self.assertEqual(message.payload, expected_put.payload)
        self.assertEqual(message.options, expected_put.options)
        print self.tr.written
        datagram, source = self.tr.written[2]
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

    def _test_separate(self, message, notification):
        serializer = Serializer()
        datagram = serializer.serialize(message)
        self.proto.datagramReceived(datagram, ("127.0.0.1", 5600))
        datagram, source = self.tr.written[0]
        host, port = source
        message = serializer.deserialize(datagram, host, port)

        self.assertEqual(message.type, defines.inv_types["ACK"])
        self.assertEqual(message.code, None)
        self.assertEqual(message.mid, self.current_mid)
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
        self.proto.datagramReceived(datagram, ("127.0.0.1", 5683))
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
        req.mid = self.current_mid

        expected = Response()
        expected.type = defines.inv_types["NON"]
        expected.mid = self.current_mid
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
        req.mid = self.current_mid
        req.payload = "Created"

        expected = Response()
        expected.type = defines.inv_types["ACK"]
        expected.mid = self.current_mid
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
        req.mid = self.current_mid

        expected = Response()
        expected.type = defines.inv_types["ACK"]
        expected.mid = self.current_mid
        expected.code = defines.responses["CONTENT"]
        expected.token = None
        expected.payload = "Created"

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
        req.mid = self.current_mid

        expected = Response()
        expected.type = defines.inv_types["CON"]
        expected.code = defines.responses["CONTENT"]
        expected.token = None
        expected.payload = "Separate"

        self._test_separate(req, expected)

    # def test_observing(self):
    #     args = ("/basic",)
    #     path = args[0]
    #
    #     req = Request()
    #     req.code = defines.inv_codes['GET']
    #     req.uri_path = path
    #     req.type = defines.inv_types["CON"]
    #     req.mid = self.current_mid
    #     o = Option()
    #     o.number = defines.inv_options["Observe"]
    #     o.value = 0
    #     req.add_option(o)
    #
    #     expected = Response()
    #     expected.type = defines.inv_types["ACK"]
    #     expected.mid = self.current_mid
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
    #     req_put.mid = self.current_mid + 1
    #     req_put.payload = "Edited"
    #
    #     expected_put = Response()
    #     expected_put.type = defines.inv_types["ACK"]
    #     expected_put.mid = self.current_mid + 1
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
    #     self._test_notification(req, expected, req_put, expected_put, notification)

