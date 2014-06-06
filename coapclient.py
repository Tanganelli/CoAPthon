#!/bin/python
import getopt
import sys
from coapthon2.client.coap_protocol import HelperClient


def usage():
    print "Command:\tcoapclient.py -o[-p[-P]]"
    print "Options:"
    print "\t-o, --operation=\tGET|PUT|POST|DELETE|DISCOVER"
    print "\t-p, --path=\t\t\tPath of the request"
    print "\t-P, --payload=\t\tPayload of the request"


def callback(response):
    print "Callback"


def main():
    op = None
    path = None
    payload = None
    try:
        opts, args = getopt.getopt(sys.argv[1:], "ho:pP", ["help", "operation=", "path=", "payload="])
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

    if op == "GET":
        if path is None:
            print "Path cannot be empty for a GET request"
            usage()
            sys.exit(2)
    if op == "DELETE":
        if path is None:
            print "Path cannot be empty for a DELETE request"
            usage()
            sys.exit(2)
    elif op == "POST":
        if path is None:
            print "Path cannot be empty for a POST request"
            usage()
            sys.exit(2)
        if payload is None:
            print "Payload cannot be empty for a POST request"
            usage()
            sys.exit(2)
    elif op == "PUT":
        if path is None:
            print "Path cannot be empty for a PUT request"
            usage()
            sys.exit(2)
        if payload is None:
            print "Payload cannot be empty for a PUT request"
            usage()
            sys.exit(2)
    elif op != "DISCOVER":
        print "Operation not recognized"
        usage()
        sys.exit(2)

    client = HelperClient()
    function = client.protocol.get
    args = ("/storage",)
    kwargs = {}
    operations = [(function, args, kwargs, callback)]
    client.start(operations)


if __name__ == '__main__':
    main()