#!/usr/bin/env python
import getopt
import json
import socket
import sys
import threading
import MySQLdb
import time

from coapthon.client.helperclient import HelperClient
from coapthon.utils import parse_uri

__author__ = 'Giacomo Tanganelli'

# parameters = ['power', 'temperature', 'battery', 'radio', 'humidity', 'light']
parameters = ['temperature', 'humidity', 'light']

client = None


def usage():  # pragma: no cover
    print ("Command:\tcollectclient.py -c ")
    print ("Options:")
    print ("\t-c, --config=\t\tConfig file")


def client_callback(response):
    print ("Callback")


def client_callback_observe(response):  # pragma: no cover
    global client
    print ("Callback_observe")
    print (response.pretty_print())
    check = True
    while check:
        chosen = raw_input("Stop observing? [y/N]: ")
        if chosen != "" and not (chosen == "n" or chosen == "N" or chosen == "y" or chosen == "Y"):
            print ("Unrecognized choose.")
            continue
        elif chosen == "y" or chosen == "Y":
            while True:
                rst = raw_input("Send RST message? [Y/n]: ")
                if rst != "" and not (rst == "n" or rst == "N" or rst == "y" or rst == "Y"):
                    print ("Unrecognized choose.")
                    continue
                elif rst == "" or rst == "y" or rst == "Y":
                    client.cancel_observing(response, True)
                else:
                    client.cancel_observing(response, False)
                check = False
                break
        else:
            break


def insert_to_db(msg, table):
    elem = json.loads(msg.payload)
    # etx="0"
    for var in elem:
        name = var['n']
        if str(name) == "best_neighbor_id":
            etx = var['etx']
            print("ETX: " + str(etx))
        if str(table) != "radio":
            unit = var['u']
        try:
            times = var['bt']
        except KeyError:
            times = var['t']
        value = var['v']

        host, port = msg.source

        conf = "collectmapping.json"
        conf = open(conf, "r")
        conf = json.load(conf)
        for n in conf["nodes"]:
            if n['port'] == port:
                id_node = n['id']

        print("type: " + str(table))

        localtime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(times))

        print("valori: " + name + " " + str(value) + " " + localtime)
        # Open database connection

        db = MySQLdb.connect("localhost", "root", "Root", "data_db")
        # print("dopo connessione")
        # prepare a cursor object using cursor() method
        cursor = db.cursor()

        # Prepare SQL query to INSERT a record into the database.
        if str(table) == "radio":
            # print("dentro radio")
            if str(name) == "best_neighbor_id":
                # print("INSERT INTO {}(name, ts, value, id_node, etx)VALUES('{}', '{}', '{}', '{}', '{}')".format(str(table),name,localtime,str(value),id_node,etx))
                sql = "INSERT INTO {}(name, ts, value, id_node, etx)VALUES('{}', '{}', '{}', '{}', '{}')".format(
                    str(table), name, localtime, str(value), id_node, etx)
            else:
                # print("dentro else")
                sql = "INSERT INTO {}(name, ts, value, id_node, etx) VALUES ('{}', '{}', '{}', '{}', '{}')".format(
                    str(table), name, localtime, str(value), id_node, "0")

        else:
            sql = "INSERT INTO {}(name, ts, value, unit, id_node) VALUES ('{}', '{}', '{}', '{}', '{}')".format(
                str(table), name, localtime, str(value), str(unit), id_node)
        # print("dopo query")
        try:
            # Execute the SQL command
            cursor.execute(sql)
            # print("dopo execute")

            # Commit your changes in the database
            db.commit()
        except:
            # Rollback in case there is any error
            db.rollback()

        # disconnect from server
        db.close()


def main():  # pragma: no cover
    global client
    config = None
    wait = 0

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hc:w", ["help", "config=", "wait="])
    except getopt.GetoptError as err:
        # print help information and exit:
        print (str(err))  # will print something like "option -a not recognized"
        usage()
        sys.exit(2)
    for o, a in opts:
        if o in ("-c", "--config"):
            config = a
            print("conf: " + str(a))
        elif o in ("-w", "--wait"):
            print("dentro wait")
            wait = a
            print("wait: " + wait)
        elif o in ("-h", "--help"):
            usage()
            sys.exit()
        else:
            usage()
            sys.exit(2)

    if config is None:
        print ("Config file must be specified")
        usage()
        sys.exit(2)


    config = open(config, "r")
    config = json.load(config)
    while True:
        for n in config["nodes"]:
            for i in parameters:
                path = "coap://" + n["ip"] + ":" + str(n["port"]) + "/" + str(i)
                print("path: " + path)
                host, port, path = parse_uri(path)
                try:
                    tmp = socket.gethostbyname(host)
                    host = tmp
                except socket.gaierror:
                    pass
                client = HelperClient(server=(host, port))
                response = client.get(path, timeout=5.0)
                print "INSERT TO DB"
                try:
                    print(response.pretty_print())
                    insert_to_db(response, i)
                    client.stop()
                except AttributeError:
                    pass
        try:
            time.sleep(float(wait))
        except:
            time.sleep(30.0)


if __name__ == '__main__':  # pragma: no cover
    main()