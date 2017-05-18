#!/usr/bin/env python
import getopt
import socket
import sys

from coapthon.client.helperclient import HelperClient
from coapthon.utils import parse_uri
import six
from six.moves import input

__author__ = 'Giacomo Tanganelli'

client = None


def usage():  # pragma: no cover
    six.print_("Command:\tcoapclient.py -o -p [-P]")
    six.print_("Options:")
    six.print_("\t-o, --operation=\tGET|PUT|POST|DELETE|DISCOVER|OBSERVE")
    six.print_("\t-p, --path=\t\t\tPath of the request")
    six.print_("\t-P, --payload=\t\tPayload of the request")
    six.print_("\t-f, --payload-file=\t\tFile with payload of the request")


def client_callback(response):
    six.print_("Callback")


def client_callback_observe(response):  # pragma: no cover
    global client
    six.print_("Callback_observe")
    check = True
    while check:
        chosen = eval(input("Stop observing? [y/N]: "))
        if chosen != "" and not (chosen == "n" or chosen == "N" or chosen == "y" or chosen == "Y"):
            six.print_("Unrecognized choose.")
            continue
        elif chosen == "y" or chosen == "Y":
            while True:
                rst = eval(input("Send RST message? [Y/n]: "))
                if rst != "" and not (rst == "n" or rst == "N" or rst == "y" or rst == "Y"):
                    six.print_("Unrecognized choose.")
                    continue
                elif rst == "" or rst == "y" or rst == "Y":
                    client.cancel_observing(response, True)
                else:
                    client.cancel_observing(response, False)
                check = False
                break
        else:
            break


def main():  # pragma: no cover
    global client
    op = None
    path = None
    payload = None
    try:
        opts, args = getopt.getopt(sys.argv[1:], "ho:p:P:f:", ["help", "operation=", "path=", "payload=",
                                                               "payload_file="])
    except getopt.GetoptError as err:
        # print help information and exit:
        six.print_(str(err))  # will print something like "option -a not recognized"
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
        six.print_("Operation must be specified")
        usage()
        sys.exit(2)

    if path is None:
        six.print_("Path must be specified")
        usage()
        sys.exit(2)

    if not path.startswith("coap://"):
        six.print_("Path must be conform to coap://host[:port]/path")
        usage()
        sys.exit(2)

    host, port, path = parse_uri(path)
    try:
        tmp = socket.gethostbyname(host)
        host = tmp
    except socket.gaierror:
        pass
    client = HelperClient(server=(host, port))
    if op == "GET":
        if path is None:
            six.print_("Path cannot be empty for a GET request")
            usage()
            sys.exit(2)
        response = client.get(path)
        six.print_(response.pretty_print())
        client.stop()
    elif op == "OBSERVE":
        if path is None:
            six.print_("Path cannot be empty for a GET request")
            usage()
            sys.exit(2)
        client.observe(path, client_callback_observe)
        
    elif op == "DELETE":
        if path is None:
            six.print_("Path cannot be empty for a DELETE request")
            usage()
            sys.exit(2)
        response = client.delete(path)
        six.print_(response.pretty_print())
        client.stop()
    elif op == "POST":
        if path is None:
            six.print_("Path cannot be empty for a POST request")
            usage()
            sys.exit(2)
        if payload is None:
            six.print_("Payload cannot be empty for a POST request")
            usage()
            sys.exit(2)
        response = client.post(path, payload)
        six.print_(response.pretty_print())
        client.stop()
    elif op == "PUT":
        if path is None:
            six.print_("Path cannot be empty for a PUT request")
            usage()
            sys.exit(2)
        if payload is None:
            six.print_("Payload cannot be empty for a PUT request")
            usage()
            sys.exit(2)
        response = client.put(path, payload)
        six.print_(response.pretty_print())
        client.stop()
    elif op == "DISCOVER":
        response = client.discover()
        six.print_(response.pretty_print())
        client.stop()
    else:
        six.print_("Operation not recognized")
        usage()
        sys.exit(2)


if __name__ == '__main__':  # pragma: no cover
    main()
