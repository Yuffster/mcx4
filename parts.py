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

    def __init__(self, mc):
        self._parent = mc


class GPIO(Port):
    pass


class XBUS(Port):
    pass


class PortException(Exception): pass
