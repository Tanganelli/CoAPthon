import unittest
import threading
import socket
import re
import random
from time import sleep
from coapthon.resource_directory.resourceDirectory import ResourceDirectory
from coapthon.messages.response import Response
from coapthon.messages.request import Request
from coapthon import defines
from coapthon.serializer import Serializer
from pymongo import MongoClient
from coapthon.client.helperclient import HelperClient

__author__ = 'Carmelo Aparo'


class ResourceDirectoryTest(unittest.TestCase):

    def setUp(self):
        self.server_address = ("127.0.0.1", 5683)
        self.current_mid = random.randint(1, 1000)
        self.server = ResourceDirectory("127.0.0.1", 5683, start_mongo=False)
        self.server_thread = threading.Thread(target=self.server.listen, args=(10,))
        self.server_thread.start()
        self.delete_database()

    def tearDown(self):
        self.server.close()
        self.server_thread.join(timeout=25)
        self.server = None

    @staticmethod
    def delete_database():
        database = defines.MONGO_DATABASE
        connection = MongoClient(defines.MONGO_HOST, defines.MONGO_PORT, username=defines.MONGO_USER,
                                 password=defines.MONGO_PWD, authSource=database, authMechanism='SCRAM-SHA-1')
        collection = connection[database].resources
        try:
            collection.delete_many({})
        except:
            print("Error in delete_database")

    @staticmethod
    def parse_core_link_format(link_format):
        data = []
        while len(link_format) > 0:
            pattern = "<([^>]*)>;"
            result = re.match(pattern, link_format)
            path = result.group(1)
            link_format = link_format[result.end(1) + 2:]
            pattern = "([^<,])*"
            result = re.match(pattern, link_format)
            attributes = result.group(0)
            dict_att = {}
            if len(attributes) > 0:
                attributes = attributes.split(";")
                for att in attributes:
                    a = att.split("=")
                    if len(a) > 1:
                        if a[1].isdigit():
                            a[1] = int(a[1])
                        else:
                            a[1] = a[1].replace('"', '')
                        dict_att[a[0]] = a[1]
                    else:
                        dict_att[a[0]] = a[0]
                link_format = link_format[result.end(0) + 1:]
            tmp = {'path': path}
            dict_att.update(tmp)
            data.append(dict_att)
        return data

    def _test_check(self, message_list, timeout=0):
        serializer = Serializer()
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        for message, expected in message_list:
            if message is not None:
                datagram = serializer.serialize(message)
                sleep(timeout)
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
                if expected.content_type is not None:
                    self.assertEqual(received_message.content_type, expected.content_type)
                if expected.payload is not None:
                    expected_list = self.parse_core_link_format(expected.payload)
                    received_list = self.parse_core_link_format(received_message.payload)
                    all_list = []
                    for expected_elem in expected_list:
                        for received_elem in received_list:
                            if expected_elem['path'] == received_elem['path']:
                                all_list_elem = (expected_elem, received_elem)
                                all_list.append(all_list_elem)
                    for data in all_list:
                        for k in data[1]:
                            self.assertIn(k, data[0])
                            if (k != "lt") and (k in data[0]):
                                self.assertEqual(data[0][k], data[1][k])
                else:
                    self.assertEqual(expected.payload, received_message.payload)
        sock.close()

    def test_uri_discovery(self):
        print("Uri discovery")
        path = ".well-known/core"
        req = Request()
        req.code = defines.Codes.GET.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.content_type = 0
        req.payload = None

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CONTENT.number
        expected.token = None
        expected.content_type = defines.Content_types["application/link-format"]
        expected.payload = '</rd-lookup/res>;rt="core.rd-lookup-res";ct=40,</rd>;rt="core.rd";ct=40,' \
                           '</rd-lookup/ep>;rt="core.rd-lookup-ep";ct=40'

        self.current_mid += 1
        self._test_check([(req, expected)])

    def test_registration(self):
        print("Registration")
        path = "rd?ep=node1&con=coap://local-proxy-old.example.com:5683"
        req = Request()
        req.code = defines.Codes.POST.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.content_type = defines.Content_types["application/link-format"]
        req.payload = '</sensors/temp>;ct=41;rt="temperature-c";if="sensor";' \
                      'anchor="coap://spurious.example.com:5683",</sensors/light>;ct=41;rt="light-lux";if="sensor"'

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CREATED.number
        expected.token = None
        expected.content_type = 0
        expected.payload = None

        self.current_mid += 1
        self._test_check([(req, expected)])

    def test_lookup_res(self):
        print("Resource lookup")
        client = HelperClient(self.server_address)
        path = "rd?ep=node1&con=coap://local-proxy-old.example.com:5683"
        ct = {'content_type': defines.Content_types["application/link-format"]}
        payload = '</sensors/temp>;ct=41;rt="temperature-c";if="sensor";anchor="coap://spurious.example.com:5683",' \
                  '</sensors/light>;ct=41;rt="light-lux";if="sensor"'
        client.post(path, payload, None, None, **ct)
        client.stop()

        path = "rd-lookup/res?ep=node1&rt=temperature-c"
        req = Request()
        req.code = defines.Codes.GET.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.content_type = 0
        req.payload = None

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CONTENT.number
        expected.token = None
        expected.content_type = defines.Content_types["application/link-format"]
        expected.payload = '<coap://local-proxy-old.example.com:5683/sensors/temp>;ct=41;rt="temperature-c";' \
                           'if="sensor";anchor="coap://spurious.example.com:5683"'

        self.current_mid += 1
        self._test_check([(req, expected)])

    def test_lookup_ep(self):
        print("Endpoint lookup")
        client = HelperClient(self.server_address)
        path = "rd?ep=node1&con=coap://local-proxy-old.example.com:5683&et=oic.d.sensor"
        ct = {'content_type': defines.Content_types["application/link-format"]}
        payload = '</sensors/temp>;ct=41;rt="temperature-c";if="sensor";anchor="coap://spurious.example.com:5683",' \
                  '</sensors/light>;ct=41;rt="light-lux";if="sensor"'
        response = client.post(path, payload, None, None, **ct)
        loc_path = response.location_path
        client.stop()

        path = "rd-lookup/ep?et=oic.d.sensor"
        req = Request()
        req.code = defines.Codes.GET.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.content_type = 0
        req.payload = None

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CONTENT.number
        expected.token = None
        expected.content_type = defines.Content_types["application/link-format"]
        expected.payload = '</' + loc_path + '>;con="coap://local-proxy-old.example.com:5683";ep="node1";' \
                                             'et="oic.d.sensor";lt=500'

        self.current_mid += 1
        self._test_check([(req, expected)])

    def test_update(self):
        print("Update")
        client = HelperClient(self.server_address)
        path = "rd?ep=endpoint1&lt=500&con=coap://local-proxy-old.example.com:5683&et=oic.d.sensor"
        ct = {'content_type': defines.Content_types["application/link-format"]}
        payload = '</sensors/temp>;ct=41;rt="temperature-c";if="sensor";anchor="coap://spurious.example.com:5683",' \
                  '</sensors/light>;ct=41;rt="light-lux";if="sensor"'
        response = client.post(path, payload, None, None, **ct)
        loc_path = response.location_path
        client.stop()

        path = loc_path + "?con=coaps://new.example.com:5684"
        req = Request()
        req.code = defines.Codes.POST.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.content_type = 0
        req.payload = None

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CHANGED.number
        expected.token = None
        expected.content_type = 0
        expected.payload = None

        self.current_mid += 1
        self._test_check([(req, expected)])

    def test_read_endpoint_links(self):
        print("Read endpoint links")
        client = HelperClient(self.server_address)
        path = "rd?ep=endpoint1&lt=500&con=coap://local-proxy-old.example.com:5683&et=oic.d.sensor"
        ct = {'content_type': defines.Content_types["application/link-format"]}
        payload = '</sensors/temp>;ct=41;rt="temperature-c";if="sensor";anchor="coap://spurious.example.com:5683",' \
                  '</sensors/light>;ct=41;rt="light-lux";if="sensor"'
        response = client.post(path, payload, None, None, **ct)
        loc_path = response.location_path
        client.stop()

        path = loc_path
        req = Request()
        req.code = defines.Codes.GET.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.content_type = 0
        req.payload = None

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CONTENT.number
        expected.token = None
        expected.content_type = defines.Content_types["application/link-format"]
        expected.payload = '<coap://local-proxy-old.example.com:5683/sensors/temp>;ct=41;rt="temperature-c";' \
                           'if="sensor";anchor="coap://spurious.example.com:5683",' \
                           '<coap://local-proxy-old.example.com:5683/sensors/light>;ct=41;rt="light-lux";if="sensor"'

        self.current_mid += 1
        self._test_check([(req, expected)])

    def test_delete(self):
        print("Delete")
        client = HelperClient(self.server_address)
        path = "rd?ep=endpoint1&lt=500&con=coap://local-proxy-old.example.com:5683&et=oic.d.sensor"
        ct = {'content_type': defines.Content_types["application/link-format"]}
        payload = '</sensors/temp>;ct=41;rt="temperature-c";if="sensor";anchor="coap://spurious.example.com:5683",' \
                  '</sensors/light>;ct=41;rt="light-lux";if="sensor"'
        response = client.post(path, payload, None, None, **ct)
        loc_path = response.location_path
        client.stop()

        path = loc_path
        req = Request()
        req.code = defines.Codes.DELETE.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.content_type = 0
        req.payload = None

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.DELETED.number
        expected.token = None
        expected.content_type = 0
        expected.payload = None

        self.current_mid += 1
        self._test_check([(req, expected)])

    def test_lookup_expired_res(self):
        print("Expired resource lookup")
        client = HelperClient(self.server_address)
        path = "rd?ep=node1&con=coap://local-proxy-old.example.com:5683&lt=60"
        ct = {'content_type': defines.Content_types["application/link-format"]}
        payload = '</sensors/temp>;ct=41;rt="temperature-c";if="sensor";anchor="coap://spurious.example.com:5683",' \
                  '</sensors/light>;ct=41;rt="light-lux";if="sensor"'
        client.post(path, payload, None, None, **ct)
        client.stop()

        path = "rd-lookup/res?ep=node1&rt=temperature-c"
        req = Request()
        req.code = defines.Codes.GET.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.content_type = 0
        req.payload = None

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CONTENT.number
        expected.token = None
        expected.content_type = defines.Content_types["application/link-format"]
        expected.payload = None

        self.current_mid += 1
        self._test_check([(req, expected)], 61)

    def test_lookup_expired_ep(self):
        print("Expired endpoint lookup")
        client = HelperClient(self.server_address)
        path = "rd?ep=node1&con=coap://local-proxy-old.example.com:5683&lt=60"
        ct = {'content_type': defines.Content_types["application/link-format"]}
        payload = '</sensors/temp>;ct=41;rt="temperature-c";if="sensor";anchor="coap://spurious.example.com:5683",' \
                  '</sensors/light>;ct=41;rt="light-lux";if="sensor"'
        client.post(path, payload, None, None, **ct)
        client.stop()

        path = "rd-lookup/ep?ep=node1&rt=temperature-c"
        req = Request()
        req.code = defines.Codes.GET.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.content_type = 0
        req.payload = None

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CONTENT.number
        expected.token = None
        expected.content_type = defines.Content_types["application/link-format"]
        expected.payload = None

        self.current_mid += 1
        # After 61 seconds the resource will be expired
        self._test_check([(req, expected)], 61)

    def test_update_expired(self):
        print("Update expired registration resource")
        client = HelperClient(self.server_address)
        path = "rd?ep=node1&con=coap://local-proxy-old.example.com:5683&lt=60"
        ct = {'content_type': defines.Content_types["application/link-format"]}
        payload = '</sensors/temp>;ct=41;rt="temperature-c";if="sensor";anchor="coap://spurious.example.com:5683",' \
                  '</sensors/light>;ct=41;rt="light-lux";if="sensor"'
        response = client.post(path, payload, None, None, **ct)
        # After 61 seconds the resource will be expired
        sleep(61)

        loc_path = response.location_path
        client.post(loc_path, None)
        client.stop()

        path = "rd-lookup/res?ep=node1&rt=temperature-c"
        req = Request()
        req.code = defines.Codes.GET.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.content_type = 0
        req.payload = None

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CONTENT.number
        expected.token = None
        expected.content_type = defines.Content_types["application/link-format"]
        expected.payload = '<coap://local-proxy-old.example.com:5683/sensors/temp>;ct=41;rt="temperature-c";' \
                           'if="sensor";anchor="coap://spurious.example.com:5683"'

        self.current_mid += 1
        self._test_check([(req, expected)])

    def test_wrong_ep(self):
        print("Endpoint name already exists")
        client = HelperClient(self.server_address)
        path = "rd?ep=node1&con=coap://local-proxy-old.example.com:5683&lt=60"
        ct = {'content_type': defines.Content_types["application/link-format"]}
        payload = '</sensors/temp>;ct=41;rt="temperature-c";if="sensor";anchor="coap://spurious.example.com:5683",' \
                  '</sensors/light>;ct=41;rt="light-lux";if="sensor"'
        client.post(path, payload, None, None, **ct)
        client.stop()

        path = "rd?ep=node1&con=coap://local-proxy-old.example.com:5683"
        req = Request()
        req.code = defines.Codes.POST.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.content_type = defines.Content_types["application/link-format"]
        req.payload = '</sensors/temp>;ct=41;rt="temperature-c";if="sensor";' \
                      'anchor="coap://spurious.example.com:5683",</sensors/light>;ct=41;rt="light-lux";if="sensor"'

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.SERVICE_UNAVAILABLE.number
        expected.token = None
        expected.content_type = 0
        expected.payload = None

        self.current_mid += 1
        self._test_check([(req, expected)])

    def test_no_ep(self):
        print("Registration without endpoint name")
        path = "rd?con=coap://local-proxy-old.example.com:5683"
        req = Request()
        req.code = defines.Codes.POST.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.content_type = defines.Content_types["application/link-format"]
        req.payload = '</sensors/temp>;ct=41;rt="temperature-c";if="sensor";' \
                      'anchor="coap://spurious.example.com:5683",</sensors/light>;ct=41;rt="light-lux";if="sensor"'

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.BAD_REQUEST.number
        expected.token = None
        expected.content_type = 0
        expected.payload = None

        self.current_mid += 1
        self._test_check([(req, expected)])

    def test_update_res_not_found(self):
        print("Resource not found on update")
        path = "rd/4521?con=coaps://new.example.com:5684"
        req = Request()
        req.code = defines.Codes.POST.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.content_type = 0
        req.payload = None

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.NOT_FOUND.number
        expected.token = None
        expected.content_type = 0
        expected.payload = None

        self.current_mid += 1
        self._test_check([(req, expected)])

    def test_delete_res_not_found(self):
        print("Resource not found on delete")
        path = "rd/4521"
        req = Request()
        req.code = defines.Codes.DELETE.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.content_type = 0
        req.payload = None

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.NOT_FOUND.number
        expected.token = None
        expected.content_type = 0
        expected.payload = None

        self.current_mid += 1
        self._test_check([(req, expected)])

    def test_wildcard_res(self):
        print("Use wildcard * to find resources")
        client = HelperClient(self.server_address)
        path = "rd?ep=node1&con=coap://local-proxy-old.example.com:5683"
        ct = {'content_type': defines.Content_types["application/link-format"]}
        payload = '</sensors/temp>;ct=41;rt="temperature-c";if="sensor";anchor="coap://spurious.example.com:5683",' \
                  '</sensors/light>;ct=41;rt="light-lux";if="sensor"'
        client.post(path, payload, None, None, **ct)
        path = "rd?ep=node2&con=coap://[2001:db8:3::123]:61616"
        payload = '</temp>;rt="temperature";anchor="coap://[2001:db8:3::123]:61616"'
        client.post(path, payload, None, None, **ct)
        client.stop()

        path = "rd-lookup/res?rt=temp*"
        req = Request()
        req.code = defines.Codes.GET.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.content_type = 0
        req.payload = None

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CONTENT.number
        expected.token = None
        expected.content_type = defines.Content_types["application/link-format"]
        expected.payload = '<coap://local-proxy-old.example.com:5683/sensors/temp>;ct=41;rt="temperature-c";' \
                           'if="sensor";anchor="coap://spurious.example.com:5683",' \
                           '<coap://[2001:db8:3::123]:61616/temp>;rt="temperature";' \
                           'anchor="coap://[2001:db8:3::123]:61616"'

        self.current_mid += 1
        self._test_check([(req, expected)])

    def test_wildcard_ep(self):
        print("Use wildcard * to find endpoints")
        client = HelperClient(self.server_address)
        path = "rd?ep=node1&con=coap://local-proxy-old.example.com:5683"
        ct = {'content_type': defines.Content_types["application/link-format"]}
        payload = '</sensors/temp>;ct=41;rt="temperature-c";if="sensor";anchor="coap://spurious.example.com:5683",' \
                  '</sensors/light>;ct=41;rt="light-lux";if="sensor"'
        response = client.post(path, payload, None, None, **ct)
        loc_path1 = response.location_path
        path = "rd?ep=node2&con=coap://[2001:db8:3::123]:61616"
        payload = '</temp>;rt="temperature";anchor="coap://[2001:db8:3::123]:61616"'
        response = client.post(path, payload, None, None, **ct)
        loc_path2 = response.location_path
        client.stop()

        path = "rd-lookup/ep?rt=temp*"
        req = Request()
        req.code = defines.Codes.GET.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.content_type = 0
        req.payload = None

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CONTENT.number
        expected.token = None
        expected.content_type = defines.Content_types["application/link-format"]
        expected.payload = '</' + loc_path1 + '>;con="coap://local-proxy-old.example.com:5683";ep="node1";lt=500,' \
                                              '</' + loc_path2 + '>;con="coap://[2001:db8:3::123]:61616";' \
                                                                 'ep="node2";lt=500'

        self.current_mid += 1
        self._test_check([(req, expected)])


if __name__ == '__main__':
    unittest.main()
