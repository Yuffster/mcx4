class Microcontroller():

    _gpios = 0
    _xbuses = 0

    _pnums = None  # {type:number}
    _ports = None  # {name:[Port,Port...]}

    def __init__(self, gpio=None, xbus=None):
        self._pnums = {'p':self._gpios, 'x':self._xbuses}
        if gpio is not None:
            self._pnums['p'] = gpio - 1
        if xbus is not None:
            self._pnums['x'] = xbus - 1
        self._ports = {'p':{}, 'x':{}}

    def __getattr__(self, name):
        # Maybe it's a port?
        if name[0] in self._pnums and name[1:].isdigit():
            return self.get_port(name)
        raise(AttributeError("Invalid attribute: {}".format(name)))

    def get_port(self, name):
        name = name.lower()
        pclass, pnum = self._normalize_port_name(name)
        ps = self._ports[name[0]]
        if pnum not in ps:
            ps[pnum] = pclass(self)
        return ps[pnum]

    def _normalize_port_name(self, name):
        """
        Takes a port name and returns its number and type.
        """
        pmap = {'p':GPIO, 'x':XBUS}
        ptype = name[0]
        pnum = name[1:]
        if ptype not in pmap:
            raise PortException("Unknown port type: "+ptype)
        if not pnum.isdigit():
            raise PortException("Invalid port number: "+pnum)
        pnum = int(pnum)
        if self._pnums[ptype] < pnum:
            raise PortException("Port out of supported range: "+name)
        return (pmap[ptype], pnum)


class Port():

    _parent = None  # Microcontroller
    _links = None  # [Port, Port...]

    def __init__(self, mc):
        self._parent = mc
        self._links = []

    def link(self, port):
        if port in self._links:
            return
        self._validate_link(port)
        self._links.append(port)
        port.link(self)

    def unlink(self, port):
        if port in self._links:
            port._links.remove(self)
            self._links.remove(port)

    def _validate_link(self, port):
        if not isinstance(port, self.__class__):
            raise PortCompatException(
                "Incompatible ports: {} / {}"
                .format(self.__class__, port.__class__)
            )
        if self.parent == port.parent:
            raise PortSelfLinkException("Part connected to self.")
        for p in self._links:
            if p.parent == self.parent:
                raise PortException("Part connected to self.")

    @property
    def parent(self):
        return self._parent


class GPIO(Port):
    pass


class XBUS(Port):
    pass


class PortException(Exception): pass
class PortSelfLinkException(PortException): pass
class PortCompatException(PortException): pass
