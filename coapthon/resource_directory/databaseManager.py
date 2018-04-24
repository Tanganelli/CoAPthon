import re
from datetime import datetime
from datetime import timedelta
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
        Establish a connection to the database.
        :param host: address of the database
        :param port: port of the database
        :param database: name of the database
        :param user: user for authentication to the database
        :param pwd: password for authentication to the database
        """
        connection = MongoClient(host, port, username=user, password=pwd, authSource=database, authMechanism='SCRAM-SHA-1')
        self.db = connection[database]
        self.rd_parameters = ["ep", "lt", "d", "con", "et", "loc_path"]

    @staticmethod
    def parse_core_link_format(link_format, rd_parameters):
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
                        if a[1].isdigit():
                            a[1] = int(a[1])
                        else:
                            a[1] = a[1].replace('"', '')
                        dict_att[a[0]] = a[1]
                    else:
                        dict_att[a[0]] = a[0]
                link_format = link_format[result.end(0) + 1:]
            tmp = {'path': path}
            tmp.update(dict_att)
            data.append(tmp)
        rd_parameters.update({'res': data})
        return rd_parameters

    @staticmethod
    def parse_uri_query(uri_query):
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
                if a[1].isdigit():
                    a[1] = int(a[1])
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
            return defines.Codes.BAD_REQUEST.number
        rd_parameters = self.parse_uri_query(endpoint)
        if "ep" not in rd_parameters:
            return defines.Codes.BAD_REQUEST.number
        if "lt" not in rd_parameters:
            rd_parameters.update({'lt': 86400})
        DatabaseManager.lock.acquire()
        loc_path = "/rd/" + str(DatabaseManager.next_loc_path)
        expiration = datetime.utcnow() + timedelta(seconds=rd_parameters['lt'])
        rd_parameters.update({'loc_path': loc_path, 'expireAt': expiration})
        data = self.parse_core_link_format(resources, rd_parameters)
        try:
            collection = self.db.resources
            collection.insert_one(data)
            DatabaseManager.next_loc_path += 1
        except (ConnectionFailure, OperationFailure):
            loc_path = defines.Codes.SERVICE_UNAVAILABLE.number
        finally:
            DatabaseManager.lock.release()
            return loc_path

    @staticmethod
    def serialize_core_link_format(cursor, type_search):
        """
        Serialize the results of a search() into a string in core link format
        :param cursor: the results of the search()
        :param type_search: it's equal to ep if the search is for endpoints or res if it is for resources
        :return: the string of results in core link format
        """
        link = ""
        first_elem = True
        previous_elem = ""
        for data in cursor:
            if not first_elem:
                link += ","
            first_elem = False
            if type_search == "ep":
                loc_path = data.pop("loc_path")
                if loc_path == previous_elem:
                    link = link[:-1]
                    continue
                previous_elem = loc_path
                data.pop('_id')
                data.pop('res')
                data['lt'] = int((data.pop('expireAt') - datetime.utcnow()).total_seconds())
                link += "<" + loc_path + ">"
            else:
                if "con" in data:
                    link += "<" + data["con"] + data["res"].pop("path") + ">"
                else:
                    link += "<" + data["res"].pop("path") + ">"
                data = data['res']
            for attr in data:
                if type(data[attr]) is int:
                    link += ";" + attr + '=' + str(data[attr])
                else:
                    link += ";" + attr + '="' + data[attr] + '"'
        return link

    def split_queries(self, query):
        query_rdp = {}
        query_res = {}
        for k in query:
            if k in self.rd_parameters:
                query_rdp[k] = query[k]
            else:
                query_res["res." + k] = query[k]
        return query_rdp, query_res

    def search(self, uri_query, type_search):
        """
        Search an endpoints or resources.
        :param uri_query: parameters to search
        :param type_search: it's equal to ep if the search is for endpoints or res if it is for resources
        :return: the string of results or an error code
        """
        if (type_search != "ep") and (type_search != "res"):
            return defines.Codes.BAD_REQUEST.number
        query = self.parse_uri_query(uri_query)
        query_rdp, query_res = self.split_queries(query)
        try:
            query = [{"$match": query_rdp}, {"$unwind": "$res"}, {"$match": query_res}]
            collection = self.db.resources
            result = collection.aggregate(query)
            link = self.serialize_core_link_format(result, type_search)
            return link
        except (ConnectionFailure, OperationFailure):
            return defines.Codes.SERVICE_UNAVAILABLE.number

    def update(self, resource, uri_query):
        """
        Update a registration resource.
        :param resource: the resource to update
        :param uri_query: the parameters of the registration resource to update
        :return: the code of the response
        """
        if len(resource) <= 0:
            return defines.Codes.BAD_REQUEST.number
        data = {}
        if len(uri_query) > 0:
            data = self.parse_uri_query(uri_query)
        res = {'loc_path': resource}
        try:
            collection = self.db.resources
            if "lt" not in data:
                lifetime = collection.find_one(res)["lt"]
            else:
                lifetime = data["lt"]
            expiration = datetime.utcnow() + timedelta(seconds=lifetime)
            data.update({"expireAt": expiration})
            result = collection.update_one(res, {"$set": data})
            if not result.matched_count:
                return defines.Codes.NOT_FOUND.number
            return defines.Codes.CHANGED.number
        except (ConnectionFailure, OperationFailure):
            return defines.Codes.SERVICE_UNAVAILABLE.number

    def delete(self, resource):
        """
        Delete an endpoint and all its resources
        :param resource: the registration resource to delete
        :return: the code of the response
        """
        res = {'loc_path': resource}
        try:
            collection = self.db.resources
            result = collection.delete_one(res)
            if not result.deleted_count:
                return defines.Codes.NOT_FOUND.number
            return defines.Codes.DELETED.number
        except (ConnectionFailure, OperationFailure):
            return defines.Codes.SERVICE_UNAVAILABLE.number
