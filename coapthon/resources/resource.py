from coapthon import defines

__author__ = 'Giacomo Tanganelli'


class Resource(object):
    """
    The Resource class. Represents the base class for all resources.
    """
    def __init__(self, name, coap_server=None, visible=True, observable=True, allow_children=True):
        """
        Initialize a new Resource.

        :param name: the name of the resource.
        :param coap_server: the server that own the resource
        :param visible: if the resource is visible
        :param observable: if the resource is observable
        :param allow_children: if the resource could has children
        """
        # The attributes of this resource.
        self._attributes = {}

        # The resource name.
        self.name = name

        # The resource path.
        self.path = None

        # Indicates whether this resource is visible to clients.
        self._visible = visible

        # Indicates whether this resource is observable by clients.
        self._observable = observable
        if self._observable:
            self._attributes["obs"] = ""

        self._allow_children = allow_children

        self._observe_count = 1

        self._payload = {}

        self._content_type = None

        self._etag = []

        self._location_query = []

        self._max_age = None

        self._coap_server = coap_server

        self._deleted = False

        self._changed = False

    @property
    def deleted(self):
        """
        Check if the resource has been deleted. For observing purpose.

        :rtype: bool
        :return: True, if deleted
        """
        return self._deleted

    @deleted.setter
    def deleted(self, b):
        """
        Set the deleted parameter. For observing purpose.

        :type b: bool
        :param b: True, if deleted
        """
        self._deleted = b

    @property
    def changed(self):
        """
        Check if the resource has been changed. For observing purpose.

        :rtype: bool
        :return: True, if changed
        """
        return self._changed

    @changed.setter
    def changed(self, b):
        """
        Set the changed parameter. For observing purpose.

        :type b: bool
        :param b: True, if changed
        """
        self._changed = b

    @property
    def etag(self):
        """
        Get the last valid ETag of the resource.

        :return: the last ETag value or None if the resource doesn't have any ETag
        """
        if self._etag:
            return self._etag[-1]
        else:
            return None

    @etag.setter
    def etag(self, etag):
        """
        Set the ETag of the resource.

        :param etag: the ETag
        """
        self._etag.append(etag)

    @property
    def location_query(self):
        """
        Get the Location-Query of a resource.

        :return: the Location-Query
        """
        return self._location_query

    @location_query.setter
    def location_query(self, lq):
        """
        Set the Location-Query.

        :param lq: the Location-Query
        """
        self._location_query = lq

    @location_query.deleter
    def location_query(self):
        """
        Delete the Location-Query.

        """
        self.location_query = []

    @property
    def max_age(self):
        """
        Get the Max-Age.

        :return: the Max-Age
        """
        return self._max_age

    @max_age.setter
    def max_age(self, ma):
        """
        Set the Max-Age.

        :param ma: the Max-Age
        """
        self._max_age = ma

    @property
    def payload(self):
        """
        Get the payload of the resource according to the content type specified by required_content_type or
        "text/plain" by default.

        :return: the payload.
        """
        if self._content_type is not None:
            try:
                return self._payload[self._content_type]
            except KeyError:
                raise KeyError("Content-Type not available")
        else:

            if defines.Content_types["text/plain"] in self._payload:
                return self._payload[defines.Content_types["text/plain"]]
            else:
                val = self._payload.keys()
                return val[0], self._payload[val[0]]

    @payload.setter
    def payload(self, p):
        """
        Set the payload of the resource.

        :param p: the new payload
        """
        if isinstance(p, tuple):
            k = p[0]
            v = p[1]
            self.actual_content_type = k
            self._payload[k] = v
        else:
            self._payload = {defines.Content_types["text/plain"]: p}

    @property
    def attributes(self):
        """
        Get the CoRE Link Format attribute of the resource.

        :return: the attribute of the resource
        """
        return self._attributes

    @attributes.setter
    def attributes(self, att):
        # TODO assert
        """
        Set the CoRE Link Format attribute of the resource.

        :param att: the attributes
        """
        self._attributes = att

    @property
    def visible(self):
        """
        Get if the resource is visible.

        :return: True, if visible
        """
        return self._visible

    @property
    def observable(self):
        """
        Get if the resource is observable.

        :return: True, if observable
        """
        return self._observable

    @property
    def allow_children(self):
        """
        Get if the resource allow children.

        :return: True, if allow children
        """
        return self._allow_children

    @property
    def observe_count(self):
        """
        Get the Observe counter.

        :return: the Observe counter value
        """
        return self._observe_count

    @observe_count.setter
    def observe_count(self, v):
        """
        Set the Observe counter.

        :param v: the Observe counter value
        """
        assert isinstance(v, int)
        self._observe_count = (v % 65000)

    @property
    def actual_content_type(self):
        """
        Get the actual required Content-Type.

        :return: the actual required Content-Type.
        """
        return self._content_type

    @actual_content_type.setter
    def actual_content_type(self, act):
        """
        Set the actual required Content-Type.

        :param act: the actual required Content-Type.
        """
        self._content_type = act

    @property
    def content_type(self):
        """
        Get the CoRE Link Format ct attribute of the resource.

        :return: the CoRE Link Format ct attribute
        """
        value = ""
        lst = self._attributes.get("ct")
        if lst is not None and len(lst) > 0:
            value = "ct="
            for v in lst:
                value += str(v) + " "
        if len(value) > 0:
            value = value[:-1]
        return value

    @content_type.setter
    def content_type(self, lst):
        """
        Set the CoRE Link Format ct attribute of the resource.

        :param lst: the list of CoRE Link Format ct attribute of the resource
        """
        value = []
        if isinstance(lst, str):
            ct = defines.Content_types[lst]
            self.add_content_type(ct)
        elif isinstance(lst, list):
            for ct in lst:
                self.add_content_type(ct)

    def add_content_type(self, ct):
        """
        Add a CoRE Link Format ct attribute to the resource.

        :param ct: the CoRE Link Format ct attribute
        """
        lst = self._attributes.get("ct")
        if lst is None:
            lst = []
        if isinstance(ct, str):
            ct = defines.Content_types[ct]
        lst.append(ct)
        self._attributes["ct"] = lst

    @property
    def resource_type(self):
        """
        Get the CoRE Link Format rt attribute of the resource.

        :return: the CoRE Link Format rt attribute
        """
        value = "rt="
        lst = self._attributes.get("rt")
        if lst is None:
            value = ""
        else:
            value += "\"" + str(lst) + "\""
        return value

    @resource_type.setter
    def resource_type(self, rt):
        """
        Set the CoRE Link Format rt attribute of the resource.

        :param rt: the CoRE Link Format rt attribute
        """
        if not isinstance(rt, str):
            rt = str(rt)
        self._attributes["rt"] = rt

    @property
    def interface_type(self):
        """
        Get the CoRE Link Format if attribute of the resource.

        :return: the CoRE Link Format if attribute
        """
        value = "if="
        lst = self._attributes.get("if")
        if lst is None:
            value = ""
        else:
            value += "\"" + str(lst) + "\""
        return value

    @interface_type.setter
    def interface_type(self, ift):
        """
        Set the CoRE Link Format if attribute of the resource.

        :param ift: the CoRE Link Format if attribute
        """
        if not isinstance(ift, str):
            ift = str(ift)
        self._attributes["if"] = ift

    @property
    def maximum_size_estimated(self):
        """
        Get the CoRE Link Format sz attribute of the resource.

        :return: the CoRE Link Format sz attribute
        """
        value = "sz="
        lst = self._attributes.get("sz")
        if lst is None:
            value = ""
        else:
            value += "\"" + str(lst) + "\""
        return value

    @maximum_size_estimated.setter
    def maximum_size_estimated(self, sz):
        """
        Set the CoRE Link Format sz attribute of the resource.

        :param sz: the CoRE Link Format sz attribute
        """
        if not isinstance(sz, str):
            sz = str(sz)
        self._attributes["sz"] = sz

    @property
    def observing(self):
        """
        Get the CoRE Link Format obs attribute of the resource.

        :return: the CoRE Link Format obs attribute
        """
        if self._observable:
            return "obs"

    def init_resource(self, request, res):
        """
        Helper function to initialize a new resource.

        :param request: the request that generate the new resource
        :param res: the resource
        :return: the edited resource
        """
        res.location_query = request.uri_query
        res.payload = (request.content_type, request.payload)
        return res

    def edit_resource(self, request):
        """
        Helper function to edit a resource

        :param request: the request that edit the resource
        """
        self.location_query = request.uri_query
        self.payload = (request.content_type, request.payload)

    def render_GET(self, request):
        """
        Method to be redefined to render a GET request on the resource.

        :param request: the request
        :return: the resource
        """
        raise NotImplementedError

    def render_GET_advanced(self, request, response):
        """
        Method to be redefined to render a GET request on the resource.

        :param response: the partially filled response
        :param request: the request
        :return: a tuple with (the resource, the response)
        """
        raise NotImplementedError

    def render_PUT(self, request):
        """
        Method to be redefined to render a PUT request on the resource.

        :param request: the request
        :return: the resource
        """
        raise NotImplementedError

    def render_PUT_advanced(self, request, response):
        """
        Method to be redefined to render a PUT request on the resource.

        :param response: the partially filled response
        :param request: the request
        :return: a tuple with (the resource, the response)
        """
        raise NotImplementedError

    def render_POST(self, request):
        """
        Method to be redefined to render a POST request on the resource.

        :param request: the request
        :return: the resource
        """
        raise NotImplementedError

    def render_POST_advanced(self, request, response):
        """
        Method to be redefined to render a POST request on the resource.

        :param response: the partially filled response
        :param request: the request
        :return: a tuple with (the resource, the response)
        """
        raise NotImplementedError

    def render_DELETE(self, request):
        """
        Method to be redefined to render a DELETE request on the resource.

        :param request: the request
        :return: a boolean
        """
        raise NotImplementedError

    def render_DELETE_advanced(self, request, response):
        """
        Method to be redefined to render a DELETE request on the resource.

        :param response: the partially filled response
        :param request: the request
        :return: a tuple with a boolean and the response
        """
        raise NotImplementedError




