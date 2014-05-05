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
            self._allow_children = name.allow_children
            self.observe_count = name.observe_count
        else:
            ## The attributes of this resource.
            self._attributes = None

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




