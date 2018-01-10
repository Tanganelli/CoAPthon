#!/usr/bin/env python
import getopt
import json
import socket
import sys

from coapthon.client.helperclient import HelperClient
from coapthon.utils import parse_uri

__author__ = 'Giacomo Tanganelli'

client = None


def usage():  # pragma: no cover
    print "Command:\tcollectclient.py -c "
    print "Options:"
    print "\t-c, --config=\t\tConfig file"


def client_callback(response):
    print "Callback"


def client_callback_observe(response):  # pragma: no cover
    global client
    print "Callback_observe"
    print response.pretty_print()
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


def main():  # pragma: no cover
    global client
    config = None
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hc:", ["help", "config="])
    except getopt.GetoptError as err:
        # print help information and exit:
        print str(err)  # will print something like "option -a not recognized"
        usage()
        sys.exit(2)
    for o, a in opts:
        if o in ("-c", "--config"):
            config = a
        elif o in ("-h", "--help"):
            usage()
            sys.exit()
        else:
            usage()
            sys.exit(2)

    if config is None:
        print "Config file must be specified"
        usage()
        sys.exit(2)

    config = open(config, "r")
    config = json.load(config)
    for n in config["nodes"]:
        path = "coap://"+n["ip"]+":"+str(n["port"])+"/radio"
        host, port, path = parse_uri(path)
        try:
            tmp = socket.gethostbyname(host)
            host = tmp
        except socket.gaierror:
            pass
        client = HelperClient(server=(host, port))
        response = client.get(path)
        print response.pretty_print()
        client.stop()

    # if op == "OBSERVE":
    #     if path is None:
    #         print "Path cannot be empty for a GET request"
    #         usage()
    #         sys.exit(2)
    #     client.observe(path, client_callback_observe)
    #
    # elif op == "DELETE":
    #     if path is None:
    #         print "Path cannot be empty for a DELETE request"
    #         usage()
    #         sys.exit(2)
    #     response = client.delete(path)
    #     print response.pretty_print()
    #     client.stop()
    # elif op == "POST":
    #     if path is None:
    #         print "Path cannot be empty for a POST request"
    #         usage()
    #         sys.exit(2)
    #     if payload is None:
    #         print "Payload cannot be empty for a POST request"
    #         usage()
    #         sys.exit(2)
    #     response = client.post(path, payload)
    #     print response.pretty_print()
    #     client.stop()
    # elif op == "PUT":
    #     if path is None:
    #         print "Path cannot be empty for a PUT request"
    #         usage()
    #         sys.exit(2)
    #     if payload is None:
    #         print "Payload cannot be empty for a PUT request"
    #         usage()
    #         sys.exit(2)
    #     response = client.put(path, payload)
    #     print response.pretty_print()
    #     client.stop()
    # elif op == "DISCOVER":
    #     response = client.discover()
    #     print response.pretty_print()
    #     client.stop()
    # else:
    #     print "Operation not recognized"
    #     usage()
    #     sys.exit(2)


if __name__ == '__main__':  # pragma: no cover
    main()
