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
        ptype = name[0]
        pnum = name[1:]
        if ptype not in self._ports:
            raise PortException("Unknown port type: "+ptype)
        if not pnum.isdigit():
            raise PortException("Invalid port number: "+pnum)
        pnum = int(pnum)
        if self._pnums[ptype] < pnum:
            raise PortException("Port out of supported range: "+name)
        ps = self._ports[ptype]
        if pnum not in ps:
            if ptype == "p":
                ps[pnum] = GPIO()
            else:
                ps[pnum] = XBUS()
        return ps[pnum]


class Port():
    pass


class GPIO(Port):
    pass


class XBUS(Port):
    pass


class PortException(Exception): pass
