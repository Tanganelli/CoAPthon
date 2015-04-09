#!/bin/python
import getopt
import sys
from coapthon.client.coap_protocol import HelperClient

client = None


def usage():
    print "Command:\tcoapclient.py -o -p [-P]"
    print "Options:"
    print "\t-o, --operation=\tGET|PUT|POST|DELETE|DISCOVER|OBSERVE"
    print "\t-p, --path=\t\t\tPath of the request"
    print "\t-P, --payload=\t\tPayload of the request"


def client_callback(response):
    print "Callback"


def client_callback_observe(response):
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
                    client.protocol.cancel_observing(response, True)
                else:
                    client.protocol.cancel_observing(response, False)
                check = False
                break
        else:
            break


def parse_uri(uri):
    t = uri.split("://")
    tmp = t[1]
    t = tmp.split("/", 1)
    tmp = t[0]
    path = t[1]
    t = tmp.split(":", 1)
    try:
        host = t[0]
        port = int(t[1])
    except IndexError:
        host = tmp
        port = 5683

    return host, port, path


def main():
    global client
    op = None
    path = None
    payload = None
    try:
        opts, args = getopt.getopt(sys.argv[1:], "ho:p:P:", ["help", "operation=", "path=", "payload="])
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
        function = client.protocol.get
        args = (path,)
        kwargs = {}
        callback = client_callback
    elif op == "OBSERVE":
        if path is None:
            print "Path cannot be empty for a GET request"
            usage()
            sys.exit(2)
        function = client.protocol.observe
        args = (path,)
        kwargs = {}
        callback = client_callback_observe
    elif op == "DELETE":
        if path is None:
            print "Path cannot be empty for a DELETE request"
            usage()
            sys.exit(2)
        function = client.protocol.delete
        args = (path,)
        kwargs = {}
        callback = client_callback
    elif op == "POST":
        if path is None:
            print "Path cannot be empty for a POST request"
            usage()
            sys.exit(2)
        if payload is None:
            print "Payload cannot be empty for a POST request"
            usage()
            sys.exit(2)
        function = client.protocol.post
        args = (path, payload)
        kwargs = {}
        callback = client_callback
    elif op == "PUT":
        if path is None:
            print "Path cannot be empty for a PUT request"
            usage()
            sys.exit(2)
        if payload is None:
            print "Payload cannot be empty for a PUT request"
            usage()
            sys.exit(2)
        function = client.protocol.put
        args = (path, payload)
        kwargs = {}
        callback = client_callback
    elif op == "DISCOVER":
        function = client.protocol.discover
        args = ()
        kwargs = {}
        callback = client_callback
    else:
        print "Operation not recognized"
        usage()
        sys.exit(2)

    operations = [(function, args, kwargs, callback)]
    client.start(operations)


if __name__ == '__main__':
    main()