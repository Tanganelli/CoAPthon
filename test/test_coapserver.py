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
        req._mid = self.current_mid

        expected = Response()
        expected.type = defines.inv_types["ACK"]
        expected._mid = self.current_mid
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
        req._mid = self.current_mid + 1

        expected = Response()
        expected.type = defines.inv_types["NON"]
        expected._mid = self.current_mid + 1
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
        req._mid = self.current_mid + 2
        req.payload = "Created"

        expected = Response()
        expected.type = defines.inv_types["ACK"]
        expected._mid = self.current_mid + 2
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
        req._mid = self.current_mid + 3

        expected = Response()
        expected.type = defines.inv_types["ACK"]
        expected._mid = self.current_mid + 3
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
        req._mid = self.current_mid

        expected = Response()
        expected.type = defines.inv_types["ACK"]
        expected._mid = self.current_mid
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
        req._mid = self.current_mid

        expected = Response()
        expected.type = defines.inv_types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.responses["CONTENT"]
        expected.token = None
        expected.payload = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Cras sollicitudin fermentum ornare." \
                           " Cras accumsan tellus quis dui lacinia eleifend. Proin ultrices rutrum orci vitae luctus. " \
                           "Nullam malesuada pretium elit, at aliquam odio vehicula in. Etiam nec maximus elit. Etiam " \
                           "at erat ac ex ornare feugiat. Curabitur sed malesuada orci, id aliquet nunc. Phasellus nec " \
                           "leo luctus, blandit lorem sit amet, interdum metus. Duis efficitur volutpat magna, ac " \
                           "ultricies nibh aliquet sit amet. Etiam tempor egestas augue in hendrerit. Nunc eget augue " \
                           "ultricies, dignissim lacus et, vulputate dolor. Nulla eros odio, fringilla vel massa ut, " \
                           "facilisis cursus quam. Fusce faucibus lobortis congue. Fusce consectetur porta neque, id " \
                           "sollicitudin velit maximus eu. Sed pharetra leo quam, vel finibus turpis cursus ac. Aenean " \
                           "ac nisi massa. Cras commodo arcu nec ante tristique ullamcorper. Quisque eu hendrerit urna. " \
                           "Cras fringilla eros ut nunc maximus, non porta nisl mollis. Aliquam in rutrum massa. " \
                           "Praesent tristique turpis dui, at ultri"
        option = Option()
        option.number = defines.inv_options["Block2"]
        option.value = 14
        expected.add_option(option)

        req2 = Request()
        req2.code = defines.inv_codes['GET']
        req2.uri_path = path
        req2.type = defines.inv_types["CON"]
        req2._mid = self.current_mid + 1
        option = Option()
        option.number = defines.inv_options["Block2"]
        option.value = 22
        req2.add_option(option)

        expected2 = Response()
        expected2.type = defines.inv_types["ACK"]
        expected2.code = defines.responses["CONTENT"]
        expected2._mid = self.current_mid + 1
        expected2.token = None
        expected2.payload = "cies lorem fermentum at. Vivamus sit amet ornare neque, a imperdiet nisl. Quisque a " \
                            "iaculis libero, id tempus lacus. Aenean convallis est non justo consectetur, a hendrerit " \
                            "enim consequat. In accumsan ante a egestas luctus. Etiam quis neque nec eros vestibulum " \
                            "faucibus. Nunc viverra ipsum lectus, vel scelerisque dui dictum a. Ut orci enim, ultrices " \
                            "a ultrices nec, pharetra in quam. Donec accumsan sit amet eros eget fermentum.Vivamus ut " \
                            "odio ac odio malesuada accumsan. Aenean vehicula diam at tempus ornare. Phasellus dictum " \
                            "mauris a mi consequat, vitae mattis nulla fringilla. Ut laoreet tellus in nisl efficitur, " \
                            "a luctus justo tempus. Fusce finibus libero eget velit finibus iaculis. Morbi rhoncus " \
                            "purus vel vestibulum ullamcorper. Sed ac metus in urna fermentum feugiat. Nulla nunc " \
                            "diam, sodales aliquam mi id, varius porta nisl. Praesent vel nibh ac turpis rutrum " \
                            "laoreet at non odio. Phasellus ut posuere mi. Suspendisse malesuada velit nec mauris " \
                            "convallis porta. Vivamus sed ultrices sapien, at cras amet."
        option = Option()
        option.number = defines.inv_options["Block2"]
        option.value = 22
        expected2.add_option(option)
        self._test_modular([(req, expected), (req2, expected2)])

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
        req._mid = self.current_mid + 4

        expected = Response()
        expected.type = defines.inv_types["CON"]
        expected.code = defines.responses["CONTENT"]
        expected.token = None
        expected.payload = "Separate"

        self._test_separate(req, expected)

    # def _test_notification(self, lst):
    #     serializer = Serializer()
    #     for t in lst:
    #         message, expected = t
    #         send_ack = False
    #         if message is not None:
    #             datagram = serializer.serialize(message)
    #             if message.source is not None:
    #                 host, port = message.source
    #             else:
    #                 host, port = ("127.0.0.1", 5600)
    #
    #             self.proto.datagramReceived(datagram, (host, port))
    #         else:
    #             send_ack = True
    #         while True:
    #             try:
    #                 datagram, source = self.tr.written.pop(0)
    #                 break
    #             except IndexError:
    #                 continue
    #         host, port = source
    #         message = serializer.deserialize(datagram, host, port)
    #         self.assertEqual(message.type, expected.type)
    #         if not send_ack:
    #             self.assertEqual(message.mid, expected.mid)
    #         self.assertEqual(message.code, expected.code)
    #         self.assertEqual(message.source, source)
    #         self.assertEqual(message.token, expected.token)
    #         self.assertEqual(message.payload, expected.payload)
    #         self.assertEqual(message.options, expected.options)
    #         if send_ack:
    #             message = Message.new_ack(message)
    #             datagram = serializer.serialize(message)
    #             self.proto.datagramReceived(datagram, ("127.0.0.1", 5600))
    #
    #     self.tr.written = []
    #
    #     message = Message.new_ack(message)
    #     datagram = serializer.serialize(message)
    #     self.proto.datagramReceived(datagram, ("127.0.0.1", 5600))
    #
    #     self.tr.written = []
    #
    # def test_observing(self):
    #     args = ("/basic",)
    #     path = args[0]
    #
    #     req = Request()
    #     req.source = ("127.0.0.1", 5600)
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
    #     req_put.source = ("127.0.0.1", 5601)
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
    #     self._test_notification([(req, expected), (req_put, expected_put), (None, notification)])
    #
