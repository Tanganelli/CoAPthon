from Queue import Queue
import random
import socket
import threading
import unittest
from coapclient import HelperClient
from coapserver import CoAPServer
from coapthon import defines
from coapthon.messages.message import Message
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
        self.server = CoAPServer("127.0.0.1", 5683)
        self.server_thread = threading.Thread(target=self.server.listen, args=(10,))
        self.server_thread.start()
        self.queue = Queue()

    def tearDown(self):
        self.server.close()
        self.server_thread.join(timeout=25)
        self.server = None

    def _test_with_client(self, message_list):  # pragma: no cover
        client = HelperClient(self.server_address)
        for message, expected in message_list:
            if message is not None:
                received_message = client.send_request(message)
            if expected is not None:
                if expected.type is not None:
                    self.assertEqual(received_message.type, expected.type)
                if expected.mid is not None:
                    self.assertEqual(received_message.mid, expected.mid)
                self.assertEqual(received_message.code, expected.code)
                if expected.source is not None:
                    self.assertEqual(received_message.source, self.server_address)
                if expected.token is not None:
                    self.assertEqual(received_message.token, expected.token)
                if expected.payload is not None:
                    self.assertEqual(received_message.payload, expected.payload)
                if expected.options:
                    self.assertEqual(len(received_message.options), len(expected.options))
                    for o in expected.options:
                        assert isinstance(o, Option)
                        option_value = getattr(expected, o.name.lower().replace("-", "_"))
                        option_value_rec = getattr(received_message, o.name.lower().replace("-", "_"))
                        self.assertEqual(option_value, option_value_rec)
        client.stop()

    def _test_with_client_observe(self, message_list):  # pragma: no cover
        client = HelperClient(self.server_address)
        for message, expected in message_list:
            if message is not None:
                client.send_request(message, self.client_callback)
            if expected is not None:
                received_message = self.queue.get()
                if expected.type is not None:
                    self.assertEqual(received_message.type, expected.type)
                if expected.mid is not None:
                    self.assertEqual(received_message.mid, expected.mid)
                self.assertEqual(received_message.code, expected.code)
                if expected.source is not None:
                    self.assertEqual(received_message.source, self.server_address)
                if expected.token is not None:
                    self.assertEqual(received_message.token, expected.token)
                if expected.payload is not None:
                    self.assertEqual(received_message.payload, expected.payload)
                if expected.options:
                    self.assertEqual(len(received_message.options), len(expected.options))
                    for o in expected.options:
                        assert isinstance(o, Option)
                        option_value = getattr(expected, o.name.lower().replace("-", "_"))
                        option_value_rec = getattr(received_message, o.name.lower().replace("-", "_"))
                        self.assertEqual(option_value, option_value_rec)
        client.stop()

    def client_callback(self, response):
        print "Callback"
        self.queue.put(response)

    def _test_plugtest(self, message_list):  # pragma: no cover
        serializer = Serializer()
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        for message, expected in message_list:
            if message is not None:
                datagram = serializer.serialize(message)
                sock.sendto(datagram, message.destination)
            if expected is not None:
                datagram, source = sock.recvfrom(4096)
                received_message = serializer.deserialize(datagram, source)
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
                    for o in expected.options:
                        assert isinstance(o, Option)
                        option_value = getattr(expected, o.name.lower().replace("-", "_"))
                        option_value_rec = getattr(received_message, o.name.lower().replace("-", "_"))
                        self.assertEqual(option_value, option_value_rec)
        sock.close()

    def _test_datagram(self, message_list):  # pragma: no cover
        serializer = Serializer()
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        for message, expected in message_list:
            if message is not None:
                datagram, destination = message
                sock.sendto(datagram, destination)
            if expected is not None:
                datagram, source = sock.recvfrom(4096)
                received_message = serializer.deserialize(datagram, source)
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
                    for o in expected.options:
                        assert isinstance(o, Option)
                        option_value = getattr(expected, o.name.lower().replace("-", "_"))
                        option_value_rec = getattr(received_message, o.name.lower().replace("-", "_"))
                        self.assertEqual(option_value, option_value_rec)
        sock.close()

    def test_not_allowed(self):
        print "TEST_NOT_ALLOWED"
        path = "/void"
        req = Request()
        req.code = defines.Codes.GET.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.METHOD_NOT_ALLOWED.number
        expected.token = None

        exchange1 = (req, expected)

        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.POST.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.METHOD_NOT_ALLOWED.number
        expected.token = None

        exchange2 = (req, expected)

        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.PUT.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.METHOD_NOT_ALLOWED.number
        expected.token = None

        exchange3 = (req, expected)

        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.DELETE.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.METHOD_NOT_ALLOWED.number
        expected.token = None

        exchange4 = (req, expected)

        self.current_mid += 1
        self._test_with_client([exchange1, exchange2, exchange3, exchange4])

    def test_separate(self):
        print "TEST_SEPARATE"
        path = "/separate"
        req = Request()
        req.code = defines.Codes.GET.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address

        expected = Response()
        expected.type = defines.Types["CON"]
        expected._mid = None
        expected.code = defines.Codes.CONTENT.number
        expected.token = None
        expected.max_age = 60

        exchange1 = (req, expected)

        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.POST.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.payload = "POST"

        expected = Response()
        expected.type = defines.Types["CON"]
        expected._mid = None
        expected.code = defines.Codes.CHANGED.number
        expected.token = None
        expected.options = None

        exchange2 = (req, expected)

        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.PUT.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.payload = "PUT"

        expected = Response()
        expected.type = defines.Types["CON"]
        expected._mid = None
        expected.code = defines.Codes.CHANGED.number
        expected.token = None
        expected.options = None

        exchange3 = (req, expected)

        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.DELETE.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address

        expected = Response()
        expected.type = defines.Types["CON"]
        expected._mid = None
        expected.code = defines.Codes.DELETED.number
        expected.token = None

        exchange4 = (req, expected)

        self.current_mid += 1
        self._test_with_client([exchange1, exchange2, exchange3, exchange4])

    def test_post(self):
        print "TEST_POST"
        path = "/storage/new_res?id=1"
        req = Request()

        req.code = defines.Codes.POST.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.payload = "test"
        req.add_if_none_match()

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CREATED.number
        expected.token = None
        expected.payload = None
        expected.location_path = "storage/new_res"
        expected.location_query = "id=1"

        exchange1 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.GET.number
        req.uri_path = "/storage/new_res"
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.if_match = ["test", "not"]

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CONTENT.number
        expected.token = None
        expected.payload = "test"

        exchange2 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.PUT.number
        req.uri_path = "/storage/new_res"
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.if_match = ["not"]
        req.payload = "not"

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.PRECONDITION_FAILED.number
        expected.token = None

        exchange3 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.POST.number
        req.uri_path = "/storage/new_res"
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.if_match = ["not"]
        req.payload = "not"

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.PRECONDITION_FAILED.number
        expected.token = None

        exchange4 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.PUT.number
        req.uri_path = "/storage/new_res"
        req._mid = self.current_mid
        req.destination = self.server_address
        req.add_if_none_match()
        req.payload = "not"

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.PRECONDITION_FAILED.number
        expected.token = None

        exchange5 = (req, expected)
        self.current_mid += 1

        self._test_with_client([exchange1, exchange2, exchange3, exchange4, exchange5])

    def test_post_block(self):
        print "TEST_POST_BLOCK"
        path = "/storage/new_res"
        req = Request()

        req.code = defines.Codes.POST.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.payload = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Cras sollicitudin fermentum ornare. " \
                       "Cras accumsan tellus quis dui lacinia eleifend. Proin ultrices rutrum orci vitae luctus. " \
                       "Nullam malesuada pretium elit, at aliquam odio vehicula in. Etiam nec maximus elit. " \
                       "Etiam at erat ac ex ornare feugiat. Curabitur sed malesuada orci, id aliquet nunc. Phasellus " \
                       "nec leo luctus, blandit lorem sit amet, interdum metus. Duis efficitur volutpat magna, ac " \
                       "ultricies nibh aliquet sit amet. Etiam tempor egestas augue in hendrerit. Nunc eget augue " \
                       "ultricies, dignissim lacus et, vulputate dolor. Nulla eros odio, fringilla vel massa ut, " \
                       "facilisis cursus quam. Fusce faucibus lobortis congue. Fusce consectetur porta neque, id " \
                       "sollicitudin velit maximus eu. Sed pharetra leo quam, vel finibus turpis cursus ac. " \
                       "Aenean ac nisi massa. Cras commodo arcu nec ante tristique ullamcorper. Quisque eu hendrerit" \
                       " urna. Cras fringilla eros ut nunc maximus, non porta nisl mollis. Aliquam in rutrum massa." \
                       " Praesent tristique turpis dui, at ultri"
        req.block1 = (1, 1, 1024)

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = None
        expected.code = defines.Codes.REQUEST_ENTITY_INCOMPLETE.number
        expected.token = None
        expected.payload = None

        exchange1 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.POST.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.payload = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Cras sollicitudin fermentum ornare. " \
                       "Cras accumsan tellus quis dui lacinia eleifend. Proin ultrices rutrum orci vitae luctus. " \
                       "Nullam malesuada pretium elit, at aliquam odio vehicula in. Etiam nec maximus elit. " \
                       "Etiam at erat ac ex ornare feugiat. Curabitur sed malesuada orci, id aliquet nunc. Phasellus " \
                       "nec leo luctus, blandit lorem sit amet, interdum metus. Duis efficitur volutpat magna, ac " \
                       "ultricies nibh aliquet sit amet. Etiam tempor egestas augue in hendrerit. Nunc eget augue " \
                       "ultricies, dignissim lacus et, vulputate dolor. Nulla eros odio, fringilla vel massa ut, " \
                       "facilisis cursus quam. Fusce faucibus lobortis congue. Fusce consectetur porta neque, id " \
                       "sollicitudin velit maximus eu. Sed pharetra leo quam, vel finibus turpis cursus ac. " \
                       "Aenean ac nisi massa. Cras commodo arcu nec ante tristique ullamcorper. Quisque eu hendrerit" \
                       " urna. Cras fringilla eros ut nunc maximus, non porta nisl mollis. Aliquam in rutrum massa." \
                       " Praesent tristique turpis dui, at ultri"
        req.block1 = (0, 1, 1024)

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = None
        expected.code = defines.Codes.CONTINUE.number
        expected.token = None
        expected.payload = None
        expected.block1 = (0, 1, 1024)

        exchange2 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.POST.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.payload = "a imperdiet nisl. Quisque a iaculis libero, id tempus lacus. Aenean convallis est non justo " \
                       "consectetur, a hendrerit enim consequat. In accumsan ante a egestas luctus. Etiam quis neque " \
                       "nec eros vestibulum faucibus. Nunc viverra ipsum lectus, vel scelerisque dui dictum a. Ut orci " \
                       "enim, ultrices a ultrices nec, pharetra in quam. Donec accumsan sit amet eros eget fermentum."
        req.block1 = (1, 1, 64)

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = None
        expected.code = defines.Codes.CONTINUE.number
        expected.token = None
        expected.payload = None
        expected.block1 = (1, 1, 64)

        exchange3 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.POST.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.payload = "a imperdiet nisl. Quisque a iaculis libero, id tempus lacus. Aenean convallis est non justo " \
                       "consectetur, a hendrerit enim consequat. In accumsan ante a egestas luctus. Etiam quis neque " \
                       "nec eros vestibulum faucibus. Nunc viverra ipsum lectus, vel scelerisque dui dictum a. Ut orci " \
                       "enim, ultrices a ultrices nec, pharetra in quam. Donec accumsan sit amet eros eget fermentum."
        req.block1 = (3, 1, 64)

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = None
        expected.code = defines.Codes.REQUEST_ENTITY_INCOMPLETE.number
        expected.token = None
        expected.payload = None

        exchange4 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.POST.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.payload = "a imperdiet nisl. Quisque a iaculis libero, id tempus lacus. Aenean convallis est non justo " \
                       "consectetur, a hendrerit enim consequat. In accumsan ante a egestas luctus. Etiam quis neque " \
                       "nec eros vestibulum faucibus. Nunc viverra ipsum lectus, vel scelerisque dui dictum a. Ut orci " \
                       "enim, ultrices a ultrices nec, pharetra in quam. Donec accumsan sit amet eros eget fermentum."
        req.block1 = (2, 0, 64)

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = None
        expected.code = defines.Codes.CREATED.number
        expected.token = None
        expected.payload = None
        expected.location_path = "storage/new_res"

        exchange5 = (req, expected)
        self.current_mid += 1

        self._test_plugtest([exchange1, exchange2, exchange3, exchange4, exchange5])

    def test_get_block(self):
        print "TEST_GET_BLOCK"
        path = "/big"

        req = Request()
        req.code = defines.Codes.GET.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.payload = None
        req.block2 = (0, 0, 512)

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = None
        expected.code = defines.Codes.CONTENT.number
        expected.token = None
        expected.payload = None
        expected.block2 = (0, 1, 512)

        exchange1 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.GET.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.payload = None
        req.block2 = (1, 0, 256)

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = None
        expected.code = defines.Codes.CONTENT.number
        expected.token = None
        expected.payload = None
        expected.block2 = (1, 1, 256)

        exchange2 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.GET.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.payload = None
        req.block2 = (2, 0, 128)

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = None
        expected.code = defines.Codes.CONTENT.number
        expected.token = None
        expected.payload = None
        expected.block2 = (2, 1, 128)

        exchange3 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.GET.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.payload = None
        req.block2 = (3, 0, 64)

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = None
        expected.code = defines.Codes.CONTENT.number
        expected.token = None
        expected.payload = None
        expected.block2 = (3, 1, 64)

        exchange4 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.GET.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.payload = None
        req.block2 = (4, 0, 32)

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = None
        expected.code = defines.Codes.CONTENT.number
        expected.token = None
        expected.payload = None
        expected.block2 = (4, 1, 32)

        exchange5 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.GET.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.payload = None
        req.block2 = (5, 0, 16)

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = None
        expected.code = defines.Codes.CONTENT.number
        expected.token = None
        expected.payload = None
        expected.block2 = (5, 1, 16)

        exchange6 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.GET.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.payload = None
        req.block2 = (6, 0, 1024)

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = None
        expected.code = defines.Codes.CONTENT.number
        expected.token = None
        expected.payload = None
        expected.block2 = (6, 1, 1024)

        exchange7 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.GET.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.payload = None
        req.block2 = (7, 0, 1024)

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = None
        expected.code = defines.Codes.CONTENT.number
        expected.token = None
        expected.payload = None
        expected.block2 = (7, 0, 1024)

        exchange8 = (req, expected)
        self.current_mid += 1

        self._test_plugtest([exchange1, exchange2, exchange3, exchange4, exchange5, exchange6, exchange7, exchange8])

    def test_post_block_big(self):
        print "TEST_POST_BLOCK_BIG"
        path = "/big"
        req = Request()

        req.code = defines.Codes.POST.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.payload = "Lorem ipsum dolo"
        req.block1 = (0, 1, 16)

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = None
        expected.code = defines.Codes.CONTINUE.number
        expected.token = None
        expected.payload = None
        expected.block1 = (0, 1, 16)

        exchange1 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.POST.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.payload = "r sit amet, consectetur adipisci"
        req.block1 = (1, 1, 32)

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = None
        expected.code = defines.Codes.CONTINUE.number
        expected.token = None
        expected.payload = None
        expected.block1 = (1, 1, 32)

        exchange2 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.POST.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.payload = "ng elit. Sed ut ultrices ligula. Pellentesque purus augue, cursu"
        req.block1 = (2, 1, 64)

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = None
        expected.code = defines.Codes.CONTINUE.number
        expected.token = None
        expected.payload = None
        expected.block1 = (2, 1, 64)

        exchange3 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.POST.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.payload = "s ultricies est in, vehicula congue metus. Vestibulum vel justo lacinia, porttitor quam vitae, " \
                      "feugiat sapien. Quisque finibus, "
        req.block1 = (3, 1, 128)

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = None
        expected.code = defines.Codes.CONTINUE.number
        expected.token = None
        expected.payload = None
        expected.block1 = (3, 1, 128)

        exchange4 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.POST.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.payload = "nisi vitae rhoncus malesuada, augue mauris dapibus tellus, sit amet venenatis libero" \
                      " libero sed lorem. In pharetra turpis sed eros porta mollis. Quisque dictum dolor nisl," \
                      " imperdiet tincidunt augue malesuada vitae. Donec non felis urna. Suspendisse at hend"
        req.block1 = (4, 1, 256)

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = None
        expected.code = defines.Codes.CONTINUE.number
        expected.token = None
        expected.payload = None
        expected.block1 = (4, 1, 256)

        exchange5 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.POST.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.payload = "rerit ex, quis aliquet ante. Vivamus ultrices dolor at elit tincidunt, eget fringilla " \
                      "ligula vestibulum. In molestie sagittis nibh, ut efficitur tellus faucibus non. Maecenas " \
                      "posuere elementum faucibus. Morbi nisi diam, molestie non feugiat et, elementum eget magna." \
                      " Donec vel sem facilisis quam viverra ultrices nec eu lacus. Sed molestie nisi id ultrices " \
                      "interdum. Curabitur pharetra sed tellus in dignissim. Duis placerat aliquam metus, volutpat " \
                      "elementum augue aliquam a. Nunc sed dolor at orci maximus portt"
        req.block1 = (5, 1, 512)

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = None
        expected.code = defines.Codes.CONTINUE.number
        expected.token = None
        expected.payload = None
        expected.block1 = (5, 1, 512)

        exchange6 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.POST.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.payload = "itor ac sit amet eros. Mauris et nisi in tortor pharetra rhoncus sit amet hendrerit metus. " \
                      "Integer laoreet placerat cursus. Nam a nulla ex. Donec laoreet sagittis libero quis " \
                      "imperdiet. Vivamus facilisis turpis nec rhoncus venenatis. Duis pulvinar tellus vel quam " \
                      "maximus imperdiet. Mauris eget nibh orci. Duis ut cursus nibh. Nulla sed commodo elit. " \
                      "Suspendisse ac eros lacinia, mattis turpis at, porttitor justo. Vivamus molestie " \
                      "tincidunt libero. Etiam porttitor lacus odio, at lobortis tortor scelerisque nec. " \
                      "Nullam non ante vel nisi ultrices consectetur. Maecenas massa felis, tempor eget " \
                      "malesuada eget, pretium eu sapien. Vivamus dapibus ante erat, non faucibus orci sodales " \
                      "sit amet. Cras magna felis, sodales eget magna sed, eleifend rutrum ligula. Vivamus interdum " \
                      "enim enim, eu facilisis tortor dignissim quis. Ut metus nulla, mattis non lorem et, " \
                      "elementum ultrices orci. Quisque eleifend, arcu vitae ullamcorper pulvinar, ipsum ex " \
                      "sodales arcu, eget consectetur mauris metus ac tortor. Donec id sem felis. Maur"
        req.block1 = (6, 0, 1024)

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = None
        expected.code = defines.Codes.CHANGED.number
        expected.token = None
        expected.payload = None
        expected.location_path = "big"

        exchange7 = (req, expected)
        self.current_mid += 1

        self._test_plugtest([exchange1, exchange2, exchange3, exchange4, exchange5, exchange6, exchange7])

    def test_options(self):
        print "TEST_OPTIONS"
        path = "/storage/new_res"

        req = Request()
        req.code = defines.Codes.POST.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        option = Option()
        option.number = defines.OptionRegistry.ETAG.number
        option.value = "test"
        req.add_option(option)
        req.del_option(option)
        req.payload = "test"

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CREATED.number
        expected.token = None
        expected.payload = None
        expected.location_path = "storage/new_res"

        exchange1 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.POST.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        option = Option()
        option.number = defines.OptionRegistry.ETAG.number
        option.value = "test"
        req.add_option(option)
        req.del_option_by_name("ETag")
        req.payload = "test"

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CREATED.number
        expected.token = None
        expected.payload = None
        expected.location_path = "storage/new_res"

        exchange2 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.POST.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        option = Option()
        option.number = defines.OptionRegistry.ETAG.number
        option.value = "test"
        req.add_option(option)
        del req.etag
        req.payload = "test"

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CREATED.number
        expected.token = None
        expected.payload = None
        expected.location_path = "storage/new_res"

        exchange3 = (req, expected)
        self.current_mid += 1

        self._test_with_client([exchange1, exchange2, exchange3])

    def test_content_type(self):
        print "TEST_CONTENT_TYPE"
        path = "/storage/new_res"

        req = Request()
        req.code = defines.Codes.POST.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.payload = "<value>test</value>"
        req.content_type = defines.Content_types["application/xml"]

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CREATED.number
        expected.token = None
        expected.payload = None
        expected.location_path = "storage/new_res"

        exchange1 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.GET.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CONTENT.number
        expected.token = None
        expected.payload = "Basic Resource"

        exchange2 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.PUT.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.payload = "test"

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CHANGED.number
        expected.token = None
        expected.payload = None

        exchange3 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.GET.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CONTENT.number
        expected.token = None
        expected.payload = "test"

        exchange4 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.GET.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.accept = defines.Content_types["application/xml"]

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CONTENT.number
        expected.token = None
        expected.payload = "<value>test</value>"
        expected.content_type = defines.Content_types["application/xml"]

        exchange5 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.GET.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.accept = defines.Content_types["application/json"]

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.NOT_ACCEPTABLE.number
        expected.token = None
        expected.payload = None

        exchange6 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.GET.number
        req.uri_path = "/xml"
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CONTENT.number
        expected.token = None
        expected.payload = "<value>0</value>"

        print(expected.pretty_print())

        exchange7 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.GET.number
        req.uri_path = "/encoding"
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CONTENT.number
        expected.token = None
        expected.payload = "0"

        exchange8 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.GET.number
        req.uri_path = "/encoding"
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.accept = defines.Content_types["application/xml"]

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CONTENT.number
        expected.token = None
        expected.payload = "<value>0</value>"
        expected.content_type = defines.Content_types["application/xml"]

        exchange9 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.GET.number
        req.uri_path = "/encoding"
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.accept = defines.Content_types["application/json"]

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CONTENT.number
        expected.token = None
        expected.payload = "{'value': '0'}"
        expected.content_type = defines.Content_types["application/json"]

        exchange10 = (req, expected)
        self.current_mid += 1

        self._test_with_client([exchange1, exchange2, exchange3, exchange4, exchange5, exchange6, exchange7,
                                exchange8, exchange9, exchange10])

    def test_ETAG(self):
        print "TEST_ETAG"
        path = "/etag"

        req = Request()
        req.code = defines.Codes.GET.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CONTENT.number
        expected.token = None
        expected.payload = "ETag resource"
        expected.etag = "0"

        exchange1 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.POST.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.payload = "test"

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CHANGED.number
        expected.token = None
        expected.payload = None
        expected.location_path = path
        expected.etag = "1"

        exchange2 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.GET.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.etag = "1"

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.VALID.number
        expected.token = None
        expected.payload = "test"
        expected.etag = "1"

        exchange3 = (req, expected)
        self.current_mid += 1

        self._test_with_client([exchange1, exchange2, exchange3])

    def test_child(self):
        print "TEST_CHILD"
        path = "/child"

        req = Request()
        req.code = defines.Codes.POST.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.payload = "test"

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CREATED.number
        expected.token = None
        expected.payload = None
        expected.location_path = path

        exchange1 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.GET.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CONTENT.number
        expected.token = None
        expected.payload = "test"

        exchange2 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.PUT.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.payload = "testPUT"

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CHANGED.number
        expected.token = None
        expected.payload = None

        exchange3 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.DELETE.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.DELETED.number
        expected.token = None
        expected.payload = None

        exchange4 = (req, expected)
        self.current_mid += 1

        self._test_with_client([exchange1, exchange2, exchange3, exchange4])

    def test_not_found(self):
        print "TEST_not_found"
        path = "/not_found"

        req = Request()
        req.code = defines.Codes.GET.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.token = 100

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.NOT_FOUND.number
        expected.token = "100"
        expected.payload = None

        exchange1 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.POST.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.payload = "test"

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.METHOD_NOT_ALLOWED.number
        expected.token = None

        exchange2 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.PUT.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.payload = "testPUT"

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.NOT_FOUND.number
        expected.token = None
        expected.payload = None

        exchange3 = (req, expected)
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.DELETE.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.NOT_FOUND.number
        expected.token = None
        expected.payload = None

        exchange4 = (req, expected)
        self.current_mid += 1

        self._test_with_client([exchange1, exchange2, exchange3, exchange4])

    def test_invalid(self):
        print "TEST_INVALID"

        # version
        req = ("\x00\x01\x8c\xda", self.server_address)

        expected = Response()
        expected.type = defines.Types["RST"]
        expected._mid = None
        expected.code = defines.Codes.BAD_REQUEST.number

        exchange1 = (req, expected)

        # version
        req = ("\x40", self.server_address)

        expected = Response()
        expected.type = defines.Types["RST"]
        expected._mid = None
        expected.code = defines.Codes.BAD_REQUEST.number

        exchange2 = (req, expected)

        # code
        req = ("\x40\x05\x8c\xda", self.server_address)

        expected = Response()
        expected.type = defines.Types["RST"]
        expected._mid = None
        expected.code = defines.Codes.BAD_REQUEST.number

        exchange3 = (req, expected)

        # option
        req = ("\x40\x01\x8c\xda\x94", self.server_address)

        expected = Response()
        expected.type = defines.Types["RST"]
        expected._mid = None
        expected.code = defines.Codes.BAD_REQUEST.number

        exchange4 = (req, expected)

        # payload marker
        req = ("\x40\x02\x8c\xda\x75\x62\x61\x73\x69\x63\xff", self.server_address)

        expected = Response()
        expected.type = defines.Types["RST"]
        expected._mid = None
        expected.code = defines.Codes.BAD_REQUEST.number

        exchange5 = (req, expected)

        self._test_datagram([exchange1, exchange2, exchange3, exchange4, exchange5])

    def test_post_block_big_client(self):
        print "TEST_POST_BLOCK_BIG_CLIENT"
        path = "/big"
        req = Request()

        req.code = defines.Codes.POST.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.payload = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Cras sollicitudin fermentum ornare. " \
                       "Cras accumsan tellus quis dui lacinia eleifend. Proin ultrices rutrum orci vitae luctus. " \
                       "Nullam malesuada pretium elit, at aliquam odio vehicula in. Etiam nec maximus elit. " \
                       "Etiam at erat ac ex ornare feugiat. Curabitur sed malesuada orci, id aliquet nunc. Phasellus " \
                       "nec leo luctus, blandit lorem sit amet, interdum metus. Duis efficitur volutpat magna, ac " \
                       "ultricies nibh aliquet sit amet. Etiam tempor egestas augue in hendrerit. Nunc eget augue " \
                       "ultricies, dignissim lacus et, vulputate dolor. Nulla eros odio, fringilla vel massa ut, " \
                       "facilisis cursus quam. Fusce faucibus lobortis congue. Fusce consectetur porta neque, id " \
                       "sollicitudin velit maximus eu. Sed pharetra leo quam, vel finibus turpis cursus ac. " \
                       "Aenean ac nisi massa. Cras commodo arcu nec ante tristique ullamcorper. Quisque eu hendrerit" \
                       " urna. Cras fringilla eros ut nunc maximus, non porta nisl mollis. Aliquam in rutrum massa." \
                       " Praesent tristique turpis dui, at ultricies lorem fermentum at. Vivamus sit amet ornare neque, " \
                       "a imperdiet nisl. Quisque a iaculis libero, id tempus lacus. Aenean convallis est non justo " \
                       "consectetur, a hendrerit enim consequat. In accumsan ante a egestas luctus. Etiam quis neque " \
                       "nec eros vestibulum faucibus. Nunc viverra ipsum lectus, vel scelerisque dui dictum a. Ut orci " \
                       "enim, ultrices a ultrices nec, pharetra in quam. Donec accumsan sit amet eros eget fermentum." \
                       "Vivamus ut odio ac odio malesuada accumsan. Aenean vehicula diam at tempus ornare. Phasellus " \
                       "dictum mauris a mi consequat, vitae mattis nulla fringilla. Ut laoreet tellus in nisl efficitur," \
                       " a luctus justo tempus. Fusce finibus libero eget velit finibus iaculis. Morbi rhoncus purus " \
                       "vel vestibulum ullamcorper. Sed ac metus in urna fermentum feugiat. Nulla nunc diam, sodales " \
                       "aliquam mi id, varius porta nisl. Praesent vel nibh ac turpis rutrum laoreet at non odio. " \
                       "Phasellus ut posuere mi. Suspendisse malesuada velit nec mauris convallis porta. Vivamus " \
                       "sed ultrices sapien, at cras amet."

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = None
        expected.code = defines.Codes.CHANGED.number
        expected.token = None
        expected.payload = None

        exchange1 = (req, expected)
        self.current_mid += 1

        self._test_with_client([exchange1])

    def test_observe_client(self):
        print "TEST_OBSERVE_CLIENT"
        path = "/basic"

        req = Request()
        req.code = defines.Codes.GET.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.observe = 0

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = None
        expected.code = defines.Codes.CONTENT.number
        expected.token = None
        expected.payload = None
        expected.observe = 1

        exchange1 = (req, expected)

        req = Message()
        req.code = defines.Codes.EMPTY.number
        req.uri_path = path
        req.type = defines.Types["RST"]
        req._mid = self.current_mid
        req.destination = self.server_address

        exchange2 = (req, None)
        self.current_mid += 1

        self._test_with_client_observe([exchange1, exchange2])

if __name__ == '__main__':
    unittest.main()

