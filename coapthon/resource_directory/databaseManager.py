import re
import logging
from time import time
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from pymongo.errors import OperationFailure
from coapthon import defines
from threading import RLock

logger = logging.getLogger(__name__)

__author__ = 'Carmelo Aparo'


class DatabaseManager(object):
    """
    Implementation of a MongoDB database manager.
    """
    lock = RLock()

    def __init__(self, host=defines.MONGO_HOST, port=defines.MONGO_PORT, database=defines.MONGO_DATABASE,
                 user=defines.MONGO_USER, pwd=defines.MONGO_PWD):
        """
        Establish a connection to the database.
        :param host: address of the database
        :param port: port of the database
        :param database: name of the database
        :param user: user for authentication to the database
        :param pwd: password for authentication to the database
        """
        connection = MongoClient(host, port, username=user, password=pwd, authSource=database,
                                 authMechanism='SCRAM-SHA-1')
        self.db = connection[database]
        self.collection = self.db.resources
        self.rd_parameters = ["ep", "lt", "d", "con", "et", "res"]

    @staticmethod
    def parse_core_link_format(link_format, rd_parameters):
        """
        Parse a string in core link format and insert the result in a dict with RD parameters.
        :param link_format: the string in core link format
        :param rd_parameters: the parameters of the registration
        :return data: list of dict that contains the result
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
        rd_parameters.update({'links': data})
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
                if a[0] == "res":
                    a[1] = a[1].strip("/")
                if a[1].isdigit():
                    a[1] = int(a[1])
                else:
                    if "*" in a[1]:
                        a[1] = {'$regex': a[1].replace('*', '')}
                dict_att[a[0]] = a[1]
            else:
                dict_att[a[0]] = a[0]
        return dict_att

    def gen_next_loc_path(self):
        """
        Generate the next location path for resource registration.
        :return: the next location path
        """
        query = [{"$sort": {"res_id": -1}}, {"$limit": 1}]
        result = self.collection.aggregate(query)
        next_loc_path = 1
        try:
            res = result.next()["res_id"]
            next_loc_path = int(res) + 1
        except StopIteration:
            logger.debug("Returned empty cursor. First document inserted.")
            next_loc_path = 1
        finally:
            return next_loc_path

    def insert(self, endpoint, resources):
        """
        Insert an endpoint and its resources.
        :param endpoint: string containing the registration parameters
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
        elif (type(rd_parameters["lt"]) is not int) or (rd_parameters["lt"] < 60) or (rd_parameters["lt"] > 4294967295):
            return defines.Codes.BAD_REQUEST.number
        with DatabaseManager.lock:
            loc_path = "rd/1"
            try:
                next_loc_path = self.gen_next_loc_path()
                loc_path = "rd/" + str(next_loc_path)
                rd_parameters.update({'res': loc_path, 'time': int(time()), 'res_id': next_loc_path})
                data = self.parse_core_link_format(resources, rd_parameters)
                self.collection.insert_one(data)
            except ConnectionFailure:
                logger.error("Connection to the database cannot be made or is lost.")
                loc_path = defines.Codes.SERVICE_UNAVAILABLE.number
            except OperationFailure:
                logger.debug("Insert operation failure. Maybe the endpoint name and the domain already exist.")
                loc_path = defines.Codes.SERVICE_UNAVAILABLE.number
            finally:
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
                loc_path = "/" + data.pop("res")
                if loc_path == previous_elem:
                    link = link[:-1]
                    continue
                previous_elem = loc_path
                data.pop('_id')
                data.pop('res_id')
                data.pop('links')
                data['lt'] = data['lt'] - (int(time()) - data.pop('time'))
                link += "<" + loc_path + ">"
            else:
                if "con" in data:
                    link += "<" + data["con"] + data["links"].pop("path") + ">"
                else:
                    link += "<" + data["links"].pop("path") + ">"
                data = data['links']
            for attr in data:
                if type(data[attr]) is int:
                    link += ";" + attr + '=' + str(data[attr])
                else:
                    if attr != data[attr]:
                        link += ";" + attr + '="' + data[attr] + '"'
                    else:
                        link += ";" + attr
        return link

    def split_queries(self, query):
        """
        Split the query in two parts, one for RD parameters and one for resource parameters
        :param query: the query to split
        :return: the dicts containing the parameters
        """
        query_rdp = {}
        query_res = {}
        for k in query:
            if k in self.rd_parameters:
                query_rdp[k] = query[k]
            else:
                query_res["links." + k] = query[k]
        return query_rdp, query_res

    def search(self, uri_query, type_search):
        """
        Search endpoints or resources.
        :param uri_query: parameters to search
        :param type_search: it's equal to ep if the search is for endpoints or res if it is for resources
        :return: the string of results or an error code
        """
        if (type_search != "ep") and (type_search != "res"):
            return defines.Codes.BAD_REQUEST.number
        if len(uri_query) <= 0:
            uri_query = "ep=*"
        query = self.parse_uri_query(uri_query)
        query_rdp, query_res = self.split_queries(query)
        try:
            query = [{"$match": {"$and": [query_rdp, {"$expr": {"$gt": [{"$sum": ["$lt", "$time"]}, int(time())]}}]}},
                     {"$unwind": "$links"}, {"$match": query_res}]
            result = self.collection.aggregate(query)
            link = self.serialize_core_link_format(result, type_search)
            return link
        except ConnectionFailure:
            logger.error("Connection to the database cannot be made or is lost.")
            return defines.Codes.SERVICE_UNAVAILABLE.number
        except OperationFailure:
            logger.error("Search operation failure with type of search " + type_search + " and uri query " + uri_query)
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
        res = {'res': resource}
        try:
            data.update({"time": int(time())})
            result = self.collection.update_one(res, {"$set": data})
            if not result.matched_count:
                return defines.Codes.NOT_FOUND.number
            return defines.Codes.CHANGED.number
        except ConnectionFailure:
            logger.error("Connection to the database cannot be made or is lost.")
            return defines.Codes.SERVICE_UNAVAILABLE.number
        except OperationFailure:
            logger.error("Update operation failure on resource " + resource + " and with uri query " + uri_query)
            return defines.Codes.SERVICE_UNAVAILABLE.number

    def delete(self, resource):
        """
        Delete an endpoint and all its resources
        :param resource: the registration resource to delete
        :return: the code of the response
        """
        res = {'res': resource}
        try:
            result = self.collection.delete_one(res)
            if not result.deleted_count:
                return defines.Codes.NOT_FOUND.number
            return defines.Codes.DELETED.number
        except ConnectionFailure:
            logger.error("Connection to the database cannot be made or is lost.")
            return defines.Codes.SERVICE_UNAVAILABLE.number
        except OperationFailure:
            logger.error("Delete operation failure on resource " + resource)
            return defines.Codes.SERVICE_UNAVAILABLE.number

    def delete_expired(self):
        """
        Deletes all the expired resources.
        """
        query = {"$expr": {"$lte": [{"$sum": ["$lt", "$time"]}, time()]}}
        try:
            self.collection.delete_many(query)
        except ConnectionFailure:
            logger.error("Connection to the database cannot be made or is lost.")
            return
        except OperationFailure:
            logger.error("Delete expired resources operation failure.")
            return
