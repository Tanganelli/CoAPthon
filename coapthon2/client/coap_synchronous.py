import random
import re
import socket
import threading
import time
from coapthon2.messages.message import Message
from coapthon2.messages.response import Response
from coapthon2 import defines
from coapthon2.serializer import Serializer
from coapthon2.messages.request import Request
from twisted.python import log


__author__ = 'giacomo'


class HelperClientSynchronous(object):
    def __init__(self):
        self._currentMID = 100
        self.relation = {}
        self.received = {}
        self.sent = {}
        self.sent_token = {}
        self.received_token = {}
        self.call_id = {}
        self._response = None
        self.condition = threading.Condition()
        self._endpoint = None
        self._socket = None
        self._receiver_thread = None
        self.stop = False

    def send(self, request, endpoint, resend=False):

        self._endpoint = endpoint
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._receiver_thread = threading.Thread(target=self.datagram_received)
        self._receiver_thread.start()
        if not resend:
            if request.mid is None:
                request.mid = self._currentMID
                self._currentMID += 1
            key = hash(str(self._endpoint[0]) + str(self._endpoint[1]) + str(request.mid))
            key_token = hash(str(self._endpoint[0]) + str(self._endpoint[1]) + str(request.token))
            self.sent[key] = (request, time.time())
            self.sent[key_token] = request
        if request.type is None:
            request.type = defines.inv_types["CON"]
        serializer = Serializer()
        request.destination = self._endpoint
        host, port = request.destination
        print "Message sent to " + host + ":" + str(port)
        print "----------------------------------------"
        print request
        print "----------------------------------------"
        datagram = serializer.serialize(request)
        log.msg("Send datagram")
        self._socket.sendto(datagram, self._endpoint)

    def schedule_retrasmission(self, request):
        host, port = self._endpoint
        if request.type == defines.inv_types['CON']:
            future_time = random.uniform(defines.ACK_TIMEOUT, (defines.ACK_TIMEOUT * defines.ACK_RANDOM_FACTOR))
            key = hash(str(host) + str(port) + str(request.mid))
            self.call_id[key] = (threading.Timer(future_time, self.retransmit, (request, host, port, future_time)), 0)

    def retransmit(self, t):
        log.msg("Retransmit")
        request, host, port, future_time = t
        key = hash(str(host) + str(port) + str(request.mid))
        call_id, retransmit_count = self.call_id[key]
        if retransmit_count < defines.MAX_RETRANSMIT and (not request.acknowledged and not request.rejected):
            retransmit_count += 1
            self.sent[key] = (request, time.time())
            self.send(request)
            future_time *= 2
            self.call_id[key] = (threading.Timer(future_time, self.retransmit,
                                                 (request, host, port, future_time)), retransmit_count)

        elif request.acknowledged or request.rejected:
            request.timeouted = False
            del self.call_id[key]
        else:
            request.timeouted = True
            log.err("Request timeouted")
            del self.call_id[key]
            # notify timeout
            self.condition.acquire()
            self.condition.notify()
            self.condition.release()

    def datagram_received(self):
        # TODO mutex
        self.stop = False
        while not self.stop:
            self._socket.settimeout(2 * defines.ACK_TIMEOUT)
            try:
                datagram, addr = self._socket.recvfrom(1152)
            except socket.timeout, e:
                err = e.args[0]
                # this next if/else is a bit redundant, but illustrates how the
                # timeout exception is setup
                if err == 'timed out':
                    print 'recv timed out, retry later'
                    continue
                else:
                    print e
                    return
            except socket.error, e:
                # Something else happened, handle error, exit, etc.
                print e
                return
            else:
                if len(datagram) == 0:
                    print 'orderly shutdown on server end'
                    return

            serializer = Serializer()
            host, port = addr
            message = serializer.deserialize(datagram, host, port)
            print "Message received from " + host + ":" + str(port)
            print "----------------------------------------"
            print message
            print "----------------------------------------"
            if isinstance(message, Response):
                self.handle_response(message)
            elif isinstance(message, Request):
                log.err("Received request")
            else:
                self.handle_message(message)
            key = hash(str(host) + str(port) + str(message.mid))
            if message.type == defines.inv_types["ACK"] and message.code == defines.inv_codes["EMPTY"] \
               and key in self.sent.keys():
                # Separate Response
                # handle separate
                print "Separate Response"
                self._response = message
                self.condition.acquire()
                self.condition.notify()
                self.condition.release()
            else:
                # TODO handle notification
                self._response = message
                self.condition.acquire()
                self.condition.notify()
                self.condition.release()
                if message.observe == 0:
                    self._receiver_thread = None
                    self.stop = True

    def handle_response(self, response):
        if response.type == defines.inv_types["CON"]:
            ack = Message.new_ack(response)
            self.send(ack, self._endpoint)
        key_token = hash(str(self._endpoint[0]) + str(self._endpoint[1]) + str(response.token))
        if key_token in self.sent_token.keys():
            self.received_token[key_token] = response
            req = self.sent_token[key_token]
            key = hash(str(self._endpoint[0]) + str(self._endpoint[1]) + str(req.mid))
            timer, counter = self.call_id[key]
            timer.cancel()
            self.received[key] = response
            self.condition.acquire()
            self._response = response
            self.condition.notify()
            self.condition.release()

    def handle_message(self, message):
        key = hash(str(self._endpoint[0]) + str(self._endpoint[1]) + str(message.mid))
        if message.type == defines.inv_types["ACK"] and message.code == defines.inv_codes["EMPTY"] \
           and key in self.sent.keys():
            return None
        if key in self.sent.keys():
            self.received[key] = message
            if message.type == defines.inv_types["RST"]:
                self._response = message
            else:
                log.err("Received unattended message")
                # handle error
                self._response = "Received unattended message"
            self.condition.acquire()
            self.condition.notify()
            self.condition.release()
    @staticmethod
    def parse_path(path):
        m = re.match("([a-zA-Z]{4,5})://([a-zA-Z0-9.]*):([0-9]*)/(\S*)", path)
        if m is None:
            m = re.match("([a-zA-Z]{4,5})://([a-zA-Z0-9.]*)/(\S*)", path)
            if m is None:
                m = re.match("([a-zA-Z]{4,5})://([a-zA-Z0-9.]*)", path)
                ip = m.group(2)
                port = 5683
                path = ""
            else:
                ip = m.group(2)
                port = 5683
                path = m.group(3)
        else:
            ip = m.group(2)
            port = int(m.group(3))
            path = m.group(4)

        return ip, port, path

    def get(self, *args, **kwargs):
        """

        :param args: request object
        :param kwargs: dictionary with parameters
        """
        if len(args) > 0:
            request = args[0]
            assert(isinstance(request, Request))
            endpoint = request.destination
            ip, port = endpoint
        else:
            request = Request()
            path = kwargs['path']
            assert(isinstance(path, str))
            ip, port, path = self.parse_path(path)
            request.destination = (ip, port)
            request.uri_path = path
            endpoint = (ip, port)
        request.code = defines.inv_codes["GET"]
        self.send(request, endpoint)
        future_time = random.uniform(defines.ACK_TIMEOUT, (defines.ACK_TIMEOUT * defines.ACK_RANDOM_FACTOR))
        retransmit_count = 0
        self.condition.acquire()
        while True:
            self.condition.wait(timeout=future_time)
            if self._response is not None:
                break
            if request.type == defines.inv_types['CON']:
                if retransmit_count < defines.MAX_RETRANSMIT and (not request.acknowledged and not request.rejected):
                    print("retransmit")
                    retransmit_count += 1
                    future_time *= 2
                    self.send(request, endpoint)
                else:
                    print("Give up on message: " + str(request.mid))
                    self.stop = True
                    break
        message = self._response
        self._response = None
        key = hash(str(ip) + str(port) + str(message.mid))
        if message.type == defines.inv_types["ACK"] and message.code == defines.inv_codes["EMPTY"] \
                and key in self.sent.keys():
            # Separate Response
            self.condition.acquire()
            self.condition.wait()
            message = self._response
            self._response = None
        return message

    def observe(self, *args, **kwargs):
        """

        :param args: request object
        :param kwargs: dictionary with parameters
        """
        if len(args) > 0:
            request = args[0]
            assert(isinstance(request, Request))
            endpoint = request.destination
        else:
            request = Request()
            path = kwargs['path']
            assert(isinstance(path, str))
            ip, port, path = self.parse_path(path)
            request.destination = (ip, port)
            request.uri_path = path
            endpoint = (ip, port)
        request.code = defines.inv_codes["GET"]
        request.observe = 0
        self.send(request, endpoint)

    def notification(self,  *args, **kwargs):
        if len(args) > 0:
            request = args[0]
            assert(isinstance(request, Request))
            endpoint = request.destination
            ip, port = endpoint
        else:
            request = Request()
            path = kwargs['path']
            assert(isinstance(path, str))
            ip, port, path = self.parse_path(path)
            endpoint = (ip, port)
        self.condition.acquire()
        self.condition.wait()
        message = self._response
        key = hash(str(ip) + str(port) + str(message.mid))
        if message.type == defines.inv_types["ACK"] and message.code == defines.inv_codes["EMPTY"] \
                and key in self.sent.keys():
            # Separate Response
            self.send(request, endpoint)
            self.condition.acquire()
            self.condition.wait()
            message = self._response
        return message

    def delete(self, *args, **kwargs):
        """

        :param args: request object
        :param kwargs: dictionary with parameters
        """
        if len(args) > 0:
            request = args[0]
            assert(isinstance(request, Request))
            endpoint = request.destination
        else:
            request = Request()
            path = kwargs['path']
            assert(isinstance(path, str))
            ip, port, path = self.parse_path(path)
            request.destination = (ip, port)
            request.uri_path = path
            endpoint = (ip, port)
        request.code = defines.inv_codes["DELETE"]
        self.send(request, endpoint)
        self.condition.acquire()
        self.condition.wait()
        message = self._response
        key = hash(str(ip) + str(port) + str(message.mid))
        if message.type == defines.inv_types["ACK"] and message.code == defines.inv_codes["EMPTY"] \
                and key in self.sent.keys():
            # Separate Response
            self.send(request, endpoint)
            self.condition.acquire()
            self.condition.wait()
            message = self._response
        return message

    def post(self, *args, **kwargs):
        """

        :param args: request object
        :param kwargs: dictionary with parameters
        """
        if len(args) > 0:
            request = args[0]
            assert(isinstance(request, Request))
            endpoint = request.destination
            payload = request.payload
        else:
            request = Request()
            path = kwargs['path']
            payload = kwargs['payload']
            assert(isinstance(path, str))
            ip, port, path = self.parse_path(path)
            request.destination = (ip, port)
            request.uri_path = path
            endpoint = (ip, port)
        request.code = defines.inv_codes["POST"]
        request.payload = payload
        self.send(request, endpoint)
        self.condition.acquire()
        self.condition.wait()
        message = self._response
        key = hash(str(ip) + str(port) + str(message.mid))
        if message.type == defines.inv_types["ACK"] and message.code == defines.inv_codes["EMPTY"] \
                and key in self.sent.keys():
            # Separate Response
            self.send(request, endpoint)
            self.condition.acquire()
            self.condition.wait()
            message = self._response
        return message

    def put(self, *args, **kwargs):
        """

        :param args: request object
        :param kwargs: dictionary with parameters
        """
        if len(args) > 0:
            request = args[0]
            assert(isinstance(request, Request))
            endpoint = request.destination
            payload = request.payload
        else:
            request = Request()
            path = kwargs['path']
            payload = kwargs['payload']
            assert(isinstance(path, str))
            ip, port, path = self.parse_path(path)
            request.destination = (ip, port)
            request.uri_path = path
            endpoint = (ip, port)
        request.code = defines.inv_codes["PUT"]
        request.payload = payload
        self.send(request, endpoint)
        self.condition.acquire()
        self.condition.wait()
        message = self._response
        key = hash(str(ip) + str(port) + str(message.mid))
        if message.type == defines.inv_types["ACK"] and message.code == defines.inv_codes["EMPTY"] \
                and key in self.sent.keys():
            # Separate Response
            self.send(request, endpoint)
            self.condition.acquire()
            self.condition.wait()
            message = self._response
        return message

    def discover(self, *args, **kwargs):
        """

        :param args: request object
        :param kwargs: dictionary with parameters
        """
        if len(args) > 0:
            request = args[0]
            assert(isinstance(request, Request))
            endpoint = request.destination
        else:
            request = Request()
            path = kwargs['path']
            assert(isinstance(path, str))
            ip, port, path = self.parse_path(path)
            request.destination = (ip, port)
            if path == "":
                path = defines.DISCOVERY_URL
            request.uri_path = path
            endpoint = (ip, port)
        request.code = defines.inv_codes["GET"]
        self.send(request, endpoint)
        self.condition.acquire()
        self.condition.wait()
        message = self._response
        key = hash(str(ip) + str(port) + str(message.mid))
        if message.type == defines.inv_types["ACK"] and message.code == defines.inv_codes["EMPTY"] \
                and key in self.sent.keys():
            # Separate Response
            self.send(request, endpoint)
            self.condition.acquire()
            self.condition.wait()
            message = self._response
        return message
