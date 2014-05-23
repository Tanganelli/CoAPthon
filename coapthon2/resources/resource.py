from twisted.python import log
from coapthon2 import defines

__author__ = 'Giacomo Tanganelli'
__version__ = "2.0"


class Resource(object):
    def __init__(self, name, visible=True, observable=True, allow_children=True):
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
        else:
            ## The attributes of this resource.
            self._attributes = {}

            ## The resource name.
            self.name = name

            ## The resource path.
            self.path = None

            ## Indicates whether this resource is visible to clients.
            self._visible = visible

            ## Indicates whether this resource is observable by clients.
            self._observable = observable

            self._allow_children = allow_children

            self._observe_count = 1

            self._payload = {}

            self._required_content_type = None

            self._etag = []

    @property
    def etag(self):
        if self._etag:
            if self._observe_count != self._etag[-1]:
                self._etag.append(self._observe_count)
        else:
            self._etag.append(self._observe_count)
        return self._etag[-1]

    @property
    def payload(self):
        if self._required_content_type is not None:
            if isinstance(self._payload, dict):
                try:
                    return self._payload[self._required_content_type]
                except KeyError:
                    return -2
        else:
            if isinstance(self._payload, dict):
                if defines.inv_content_types["text/plain"] in self._payload:
                    return self._payload[defines.inv_content_types["text/plain"]]
                else:
                    val = self._payload.values()
                    return val[0]

        return self._payload

    @payload.setter
    def payload(self, p):
        if isinstance(p, dict):
            self._payload = {}
            for k in p.keys():
                v = p[k]
                self._payload[defines.inv_content_types[k]] = v
        else:
            self._payload = {defines.inv_content_types["text/plain"]: p}

    @property
    def attributes(self):
        return self._attributes

    @attributes.setter
    def attributes(self, att):
        #TODO assert
        self._attributes = att

    @property
    def visible(self):
        return self._visible

    @visible.setter
    def visible(self, v):
        assert isinstance(v, bool)
        self._visible = v

    @property
    def observable(self):
        return self._observable

    @observable.setter
    def observable(self, v):
        assert isinstance(v, bool)
        self._observable = v

    @property
    def allow_children(self):
        return self._allow_children

    @allow_children.setter
    def allow_children(self, v):
        assert isinstance(v, bool)
        self._allow_children = v

    @property
    def observe_count(self):
        return self._observe_count

    @observe_count.setter
    def observe_count(self, v):
        assert isinstance(v, int)
        self._observe_count = v

    @property
    def required_content_type(self):
        return self._required_content_type

    @required_content_type.setter
    def required_content_type(self, act):
        if isinstance(act, str):
            self._required_content_type = defines.inv_content_types[act]
        else:
            self._required_content_type = act


    @property
    def content_type(self):
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
        value = []
        if isinstance(lst, str):
            ct = defines.inv_content_types[lst]
            value.append(ct)
        else:
            for ct in lst:
                ct = defines.inv_content_types[ct]
                value.append(ct)
        if len(value) > 0:
            self._attributes["ct"] = value

    def add_content_type(self, ct):
        lst = self._attributes.get("ct")
        if lst is None:
            lst = []
        ct = defines.inv_content_types[ct]
        lst.append(ct)
        self._attributes["ct"] = lst

    @property
    def resource_type(self):
        value = "rt="
        lst = self._attributes.get("rt")
        if lst is None:
            value = ""
        else:
            value += "\"" + str(lst) + "\""
        return value

    @resource_type.setter
    def resource_type(self, rt):
        self._attributes["rt"] = rt

    @property
    def interface_type(self):
        value = "rt="
        lst = self._attributes.get("if")
        if lst is None:
            value = ""
        else:
            value += "\"" + str(lst) + "\""
        return value

    @interface_type.setter
    def interface_type(self, ift):
        self._attributes["if"] = ift

    @property
    def maximum_size_estimated(self):
        value = "sz="
        lst = self._attributes.get("sz")
        if lst is None:
            value = ""
        else:
            value += "\"" + str(lst) + "\""
        return value

    @maximum_size_estimated.setter
    def maximum_size_estimated(self, sz):
        self._attributes["sz"] = sz

    def render_GET(self, query=None):
        return -1

    def render_PUT(self, payload=None, query=None):
        return -1

    def render_POST(self, payload=None, query=None):
        return -1

    def render_DELETE(self, query=None):
        return -1

    def new_resource(self):
        return Resource("sumbtree")





