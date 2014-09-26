#!/bin/python
import getopt
import sys
import threading
from coapthon2.client.coap_synchronous import HelperClientSynchronous

client = HelperClientSynchronous()


def usage():
    print "Command:\tcoapclient.py -o[-p[-P]]"
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


def main():
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

    if op == "GET":
        if path is None:
            print "Path cannot be empty for a GET request"
            usage()
            sys.exit(2)
        kwargs = {"path": path}
        response = client.get(**kwargs)
        print response
        return
    elif op == "OBSERVE":
        if path is None:
            print "Path cannot be empty for a GET request"
            usage()
            sys.exit(2)
        kwargs = {"path": path}
        client.observe(**kwargs)
        while True:
            response = client.notification(**kwargs)
            print response
    elif op == "DELETE":
        if path is None:
            print "Path cannot be empty for a DELETE request"
            usage()
            sys.exit(2)
        kwargs = {"path": path}
        response = client.delete(**kwargs)
        print response
    elif op == "POST":
        if path is None:
            print "Path cannot be empty for a POST request"
            usage()
            sys.exit(2)
        if payload is None:
            print "Payload cannot be empty for a POST request"
            usage()
            sys.exit(2)
        kwargs = {"path": path, "payload": payload}
        response = client.post(**kwargs)
        print response
    elif op == "PUT":
        if path is None:
            print "Path cannot be empty for a PUT request"
            usage()
            sys.exit(2)
        if payload is None:
            print "Payload cannot be empty for a PUT request"
            usage()
            sys.exit(2)
        kwargs = {"path": path, "payload": payload}
        response = client.put(**kwargs)
        print response
    elif op == "DISCOVER":
        kwargs = {"path": path}
        response = client.discover(**kwargs)
        print response
    else:
        print "Operation not recognized"
        usage()
        sys.exit(2)



if __name__ == '__main__':
    main()