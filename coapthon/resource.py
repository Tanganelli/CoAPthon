from coapthon import defines


class Resource(object):
    """
    The Resource class.
    """
    def __init__(self, name, coap_server=None, visible=True, observable=True, allow_children=True):
        """
        Initialize a new Resource.

        :param name: the name or a Resource object to copy from.
        :param visible: if the resource is visible
        :param observable: if the resource is observable
        :param allow_children: if the resource could has children
        """
        if isinstance(name, Resource):
            self._attributes = name.attributes
            self.name = name.name
            self.path = name.path
            self._visible = name.visible
            self.observable = name.observable
            self._required_content_type = name.required_content_type
            self._allow_children = name.allow_children
            self.observe_count = name.observe_count
            self._payload = name.payload
            self._etag = name.etag
            self._location_query = name.location_query
            self._max_age = name.max_age
            self._coap_server = name._coap_server
            self._deleted = False
            self._changed = False
        else:
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

            self._allow_children = allow_children

            self._observe_count = 1

            self._payload = {}

            self._required_content_type = None

            self._etag = []

            self._location_query = []

            self._max_age = None

            self._coap_server = coap_server

            self._deleted = False
            self._changed = False

    @property
    def deleted(self):
        return self._deleted

    @deleted.setter
    def deleted(self, b):
        self._deleted = b

    @property
    def changed(self):
        return self._changed

    @changed.setter
    def changed(self, b):
        self._changed = b

    @property
    def etag(self):
        """
        Get the last valid ETag of the resource.

        :return: the ETag value or None if the resource doesn't have any ETag
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
        if self._required_content_type is not None:
            if isinstance(self._payload, dict):
                try:
                    return self._payload[self._required_content_type]
                except KeyError:
                    raise KeyError("Content-Type not available")
        else:
            if isinstance(self._payload, dict):
                if defines.Content_types["text/plain"] in self._payload:
                    return self._payload[defines.Content_types["text/plain"]]
                else:
                    val = self._payload.keys()
                    return val[0], self._payload[val[0]]

        return self._payload

    @payload.setter
    def payload(self, p):
        """
        Set the payload of the resource.

        :param p: the new payload
        """
        if isinstance(p, dict):
            self._payload = {}
            for k in p.keys():
                v = p[k]
                self._payload[k] = v
        else:
            self._payload = {defines.Content_types["text/plain"]: p}

    @property
    def raw_payload(self):
        """
        Get the payload of the resource as a dict of all different payloads defined for the resource.

        :return: the payload as dict
        """
        return self._payload

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

    @visible.setter
    def visible(self, v):
        """
        Set if the resource is visible.

        :param v: the visibility (True or False)
        """
        assert isinstance(v, bool)
        self._visible = v

    @property
    def observable(self):
        """
        Get if the resource is observable.

        :return: True, if observable
        """
        return self._observable

    @observable.setter
    def observable(self, v):
        """
        Set if the resource is observable.

        :param v: the observability (True or False)
        """
        assert isinstance(v, bool)
        self._observable = v

    @property
    def allow_children(self):
        """
        Get if the resource allow children.

        :return: True, if allow children
        """
        return self._allow_children

    @allow_children.setter
    def allow_children(self, v):
        """
        Set if the resource  allow children.

        :param v: the  allow children (True or False)
        """
        assert isinstance(v, bool)
        self._allow_children = v

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
        self._observe_count = v

    @property
    def required_content_type(self):
        """
        Get the actual required Content-Type.

        :return: the actual required Content-Type.
        """
        return self._required_content_type

    @required_content_type.setter
    def required_content_type(self, act):
        """
        Set the actual required Content-Type.

        :param act: the actual required Content-Type.
        """
        if isinstance(act, str):
            self._required_content_type = defines.Content_types[act]
        else:
            self._required_content_type = act

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
            value.append(ct)
        else:
            for ct in lst:
                ct = defines.Content_types[ct]
                value.append(ct)
        if len(value) > 0:
            self._attributes["ct"] = value

    def add_content_type(self, ct):
        """
        Add a CoRE Link Format ct attribute to the resource.

        :param ct: the CoRE Link Format ct attribute
        """
        lst = self._attributes.get("ct")
        if lst is None:
            lst = []
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
        self._attributes["sz"] = sz

    def render_GET(self, request):
        """
        Method to be redefined to render a GET request on the resource.

        :param request: the request
        :return: the response
        """
        raise NotImplementedError

    def render_PUT(self, request):
        """
        Method to be redefined to render a PUTT request on the resource.

        :param request: the request
        :return: the response
        """
        raise NotImplementedError

    def render_POST(self, request):
        """
        Method to be redefined to render a POST request on the resource.

        :param request: the request
        :return: the response
        """
        raise NotImplementedError

    def render_DELETE(self, request):
        """
        Method to be redefined to render a DELETE request on the resource.

        :param request: the request
        """
        raise NotImplementedError


