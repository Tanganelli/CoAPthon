import re
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from pymongo.errors import OperationFailure
from threading import Lock
from coapthon import defines

__author__ = 'Carmelo Aparo'


class DatabaseManager(object):
    next_loc_path = 1
    lock = Lock()

    def __init__(self, host="127.0.0.1", port=27017, database="resourceDirectory", user="RD", pwd="res-dir"):
        """
        Establish a connection to the database and set the boolean isconnected
        :param host: address of the database
        :param port: port of the database
        :param database: name of the database
        :param user: user for authentication to the database
        :param pwd: password for authentication to the database
        """
        connection = MongoClient(host, port, username=user, password=pwd, authSource=database, authMechanism='SCRAM-SHA-1')
        self.db = connection[database]
        self.isconnected = True
        # check if the database is available
        try:
            self.db.command("ismaster")
        except ConnectionFailure:
            print("Connection to database cannot be made or is lost")
            self.isconnected = False

    def parse_core_link_format(self, link_format, loc_path):
        """
        Parse a string in core link format and insert location path to the result.
        :param link_format: the string in core link format
        :param loc_path: the location path to add
        :return data: list of dict that contains the result of the parsing
        """
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
                        a[1] = a[1].replace('"', '')
                        dict_att[a[0]] = a[1]
                    else:
                        a[0] = a[0].replace('"', '')
                        dict_att[a[0]] = a[0]
                link_format = link_format[result.end(0) + 1:]
            tmp = {'uri': path, 'res': loc_path}
            tmp.update(dict_att)
            data.append(tmp)
        return data

    def parse_uri_query(self, uri_query):
        """
        Parse an uri query.
        :param uri_query: the string to parse
        :return: the dict with the results
        """
        dict_att = {}
        attributes = uri_query.split("&")
        for att in attributes:
            a = att.split("=")
            if len(a) > 1:
                dict_att[a[0]] = a[1]
            else:
                dict_att[a[0]] = a[0]
        return dict_att

    def insert(self, endpoint, resources):
        """
        Insert an endpoint and its resources.
        :param endpoint: string containing the endpoint and its parameters
        :param resources: string in core link format containing the resources
        :return: the location path of the registration resource or an error code
        """
        if (len(endpoint) <= 0) or (len(resources) <= 0):
            return defines.Codes.BAD_REQUEST
        data_ep = self.parse_uri_query(endpoint)
        if "ep" not in data_ep:
            return defines.Codes.BAD_REQUEST
        if "lt" not in data_ep:
            data_ep.update({'lt': '86400'})
        DatabaseManager.lock.acquire()
        loc_path = "/rd/" + str(DatabaseManager.next_loc_path)
        data_ep.update({'res': loc_path})
#       add current time to data_ep
        data_res = self.parse_core_link_format(resources, loc_path)
        try:
            collection = self.db.endpoints
            collection.insert_one(data_ep)
            collection = self.db.resources
            collection.insert_many(data_res)
            DatabaseManager.next_loc_path += 1
        except OperationFailure:
            print("OperationFailure")
            loc_path = defines.Codes.SERVICE_UNAVAILABLE
        finally:
            DatabaseManager.lock.release()
            return loc_path

    def serialize_core_link_format(self, cursor, type_search):
        """
        Serialize the results of a search() into a string in core link format
        :param cursor: the results of the search()
        :param type_search: it's equal to ep if the search is for endpoints or res if it is for resources
        :return: the string of results in core link format
        """
        link = ""
        first_elem = True
        for data in cursor:
            data.pop('_id')
#           remove time
            if not first_elem:
                link += ","
            first_elem = False
            if type_search == "ep":
                link += "<" + data.pop("res") + ">"
            elif type_search == "res":
                data.pop("res")
                link += "<" + data.pop("uri") + ">"
            else:
                return link
            keys = data.keys()
            for attr in keys:
                link += ";"
                link += attr + '="' + data[attr] + '"'
        return link

    def search(self, uri_query, type_search):
        """
        Search an endpoints or resources.
        :param uri_query: parameters to search
        :param type_search: it's equal to ep if the search is for endpoints or res if it is for resources
        :return: the string of results or an error code
        """
        query = self.parse_uri_query(uri_query)
        try:
            if type_search == "ep":
                collection = self.db.endpoints
            elif type_search == "res":
                collection = self.db.resources
            else:
                return defines.Codes.SERVICE_UNAVAILABLE
            result = collection.find(query)
            link = self.serialize_core_link_format(result, type_search)
            return link
        except OperationFailure:
            print("Operation Failure")
            return defines.Codes.SERVICE_UNAVAILABLE

    def update(self, resource, uri_query):
        """
        Update a registration resource.
        :param resource: the resource to update
        :param uri_query: the parameters of the registration resource to update
        :return: the code of the response
        """
        if len(resource) <= 0:
            return defines.Codes.BAD_REQUEST
        data = {}
        if len(uri_query) > 0:
            data = self.parse_uri_query(uri_query)
#       data.update({'time': str(time())})
        res = {'res': resource}
        try:
            collection = self.db.endpoints
            result = collection.update_one(res, {"$set": data})
            if not result.matched_count:
                print("Resource not found")
                return defines.Codes.NOT_FOUND
            return defines.Codes.CHANGED
        except OperationFailure:
            print("Operation Failure")
            return defines.Codes.SERVICE_UNAVAILABLE

    def delete(self, resource):
        """
        Delete an endpoint and all its resources
        :param resource: the registration resource to delete
        :return: the code of the response
        """
        res = {'res': resource}
        try:
            collection = self.db.endpoints
            result = collection.delete_one(res)
            if not result.deleted_count:
                print("Not found")
                return defines.Codes.NOT_FOUND
            collection = self.db.resources
            collection.delete_many(res)
            return defines.Codes.DELETED
        except OperationFailure:
            print("Operation Failure")
            return defines.Codes.SERVICE_UNAVAILABLE
