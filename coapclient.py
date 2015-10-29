#!/bin/python
from Queue import Queue
import getopt
import random
import sys
import threading
from coapthon import defines
from coapthon.client.coap import CoAP
from coapthon.messages.message import Message
from coapthon.messages.request import Request
from coapthon.utils import parse_uri

client = None


def usage():
    print "Command:\tcoapclient.py -o -p [-P]"
    print "Options:"
    print "\t-o, --operation=\tGET|PUT|POST|DELETE|DISCOVER|OBSERVE"
    print "\t-p, --path=\t\t\tPath of the request"
    print "\t-P, --payload=\t\tPayload of the request"
    print "\t-f, --payload-file=\t\tFile with payload of the request"


def client_callback(response):
    print "Callback"


def client_callback_observe(response):
    global client
    print "Callback_observe"
    check = True
    while check:
        chosen = raw_input("Stop observing? [y/N]: ")
        if chosen != "" and not (chosen == "n" or chosen == "N" or chosen == "y" or chosen == "Y"):
            print "Unrecognized choose."
            continue
        elif chosen == "y" or chosen == "Y":
            while True:
                rst = raw_input("Send RST message? [Y/n]: ")
                if rst != "" and not (rst == "n" or rst == "N" or rst == "y" or rst == "Y"):
                    print "Unrecognized choose."
                    continue
                elif rst == "" or rst == "y" or rst == "Y":
                    client.cancel_observing(response, True)
                else:
                    client.cancel_observing(response, False)
                check = False
                break
        else:
            break





class HelperClient(object):
    def __init__(self, server):
        self.server = server
        self.protocol = CoAP(self.server, random.randint(1, 65535), self._wait_response)
        self.queue = Queue()

    def _wait_response(self, message):
        if message.code != defines.Codes.CONTINUE.number:
            self.queue.put(message)

    def stop(self):
        self.protocol.stopped.set()
        self.queue.put(None)

    def _thread_body(self, request, callback):
        self.protocol.send_message(request)
        while not self.protocol.stopped.isSet():
            response = self.queue.get(block=True)
            callback(response)

    def cancel_observing(self, response, send_rst):
        if send_rst:
            message = Message()
            message.destination = self.server
            message.code = defines.Codes.EMPTY.number
            message.type = defines.Types["RST"]
            message.token = response.token
            message.mid = response.mid
            self.protocol.send_message(message)
        self.stop()

    def get(self, path, callback=None):
        request = Request()
        request.destination = self.server
        request.code = defines.Codes.GET.number
        request.uri_path = path

        if callback is not None:
            thread = threading.Thread(target=self._thread_body, args=(request, callback))
            thread.start()
        else:
            self.protocol.send_message(request)
            response = self.queue.get(block=True)
            return response

    def observe(self, path, callback):
        request = Request()
        request.destination = self.server
        request.code = defines.Codes.GET.number
        request.uri_path = path
        request.observe = 0

        if callback is not None:
            thread = threading.Thread(target=self._thread_body, args=(request, callback))
            thread.start()
        else:
            self.protocol.send_message(request)
            response = self.queue.get(block=True)
            return response

    def delete(self, path, callback=None):
        request = Request()
        request.destination = self.server
        request.code = defines.Codes.DELETE.number
        request.uri_path = path
        if callback is not None:
            thread = threading.Thread(target=self._thread_body, args=(request, callback))
            thread.start()
        else:
            self.protocol.send_message(request)
            response = self.queue.get(block=True)
            return response

    def post(self, path, payload, callback=None):
        request = Request()
        request.destination = self.server
        request.code = defines.Codes.POST.number
        request.uri_path = path
        request.payload = payload
        if callback is not None:
            thread = threading.Thread(target=self._thread_body, args=(request, callback))
            thread.start()
        else:
            self.protocol.send_message(request)
            response = self.queue.get(block=True)
            return response

    def put(self, path, payload, callback=None):
        request = Request()
        request.destination = self.server
        request.code = defines.Codes.PUT.number
        request.uri_path = path
        request.payload = payload
        if callback is not None:
            thread = threading.Thread(target=self._thread_body, args=(request, callback))
            thread.start()
        else:
            self.protocol.send_message(request)
            response = self.queue.get(block=True)
            return response

    def discover(self, callback=None):
        request = Request()
        request.destination = self.server
        request.code = defines.Codes.GET.number
        request.uri_path = defines.DISCOVERY_URL
        if callback is not None:
            thread = threading.Thread(target=self._thread_body, args=(request, callback))
            thread.start()
        else:
            self.protocol.send_message(request)
            response = self.queue.get(block=True)
            return response

    def send_request(self, request, callback=None):
        if callback is not None:
            thread = threading.Thread(target=self._thread_body, args=(request, callback))
            thread.start()
        else:
            self.protocol.send_message(request)
            response = self.queue.get(block=True)
            return response

    def send_empty(self, empty):
        self.protocol.send_message(empty)


def main():
    global client
    op = None
    path = None
    payload = None
    try:
        opts, args = getopt.getopt(sys.argv[1:], "ho:p:P:f:", ["help", "operation=", "path=", "payload=",
                                                               "payload_file="])
    except getopt.GetoptError as err:
        # print help information and exit:
        print str(err)  # will print something like "option -a not recognized"
        usage()
        sys.exit(2)
    for o, a in opts:
        if o in ("-o", "--operation"):
            op = a
        elif o in ("-p", "--path"):
            path = a
        elif o in ("-P", "--payload"):
            payload = a
        elif o in ("-f", "--payload-file"):
            with open(a, 'r') as f:
                payload = f.read()
        elif o in ("-h", "--help"):
            usage()
            sys.exit()
        else:
            usage()
            sys.exit(2)

    if op is None:
        print "Operation must be specified"
        usage()
        sys.exit(2)

    if path is None:
        print "Path must be specified"
        usage()
        sys.exit(2)

    if not path.startswith("coap://"):
        print "Path must be conform to coap://host[:port]/path"
        usage()
        sys.exit(2)

    host, port, path = parse_uri(path)
    client = HelperClient(server=(host, port))
    if op == "GET":
        if path is None:
            print "Path cannot be empty for a GET request"
            usage()
            sys.exit(2)
        response = client.get(path)
        print response.pretty_print()
        client.stop()
    elif op == "OBSERVE":
        if path is None:
            print "Path cannot be empty for a GET request"
            usage()
            sys.exit(2)
        client.observe(path, client_callback_observe)
        
    elif op == "DELETE":
        if path is None:
            print "Path cannot be empty for a DELETE request"
            usage()
            sys.exit(2)
        response = client.delete(path)
        print response.pretty_print()
        client.stop()
    elif op == "POST":
        if path is None:
            print "Path cannot be empty for a POST request"
            usage()
            sys.exit(2)
        if payload is None:
            print "Payload cannot be empty for a POST request"
            usage()
            sys.exit(2)
        response = client.post(path, payload)
        print response.pretty_print()
        client.stop()
    elif op == "PUT":
        if path is None:
            print "Path cannot be empty for a PUT request"
            usage()
            sys.exit(2)
        if payload is None:
            print "Payload cannot be empty for a PUT request"
            usage()
            sys.exit(2)
        response = client.put(path, payload)
        print response.pretty_print()
        client.stop()
    elif op == "DISCOVER":
        response = client.discover()
        print response.pretty_print()
        client.stop()
    else:
        print "Operation not recognized"
        usage()
        sys.exit(2)


if __name__ == '__main__':
    main()
