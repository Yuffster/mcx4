import exceptions as x

class Microcontroller():

    _gpios = 0
    _xbuses = 0
    
    # Registers
    _acc = 0

    _pnums = None  # {type:number}
    _ports = None  # {name:[Port,Port...]}

    _name = ""

    _part_count = 0  # static

    def __init__(self, name=None, gpio=None, xbus=None):
        self._pnums = {'p':self._gpios, 'x':self._xbuses}
        if gpio is not None:
            self._pnums['p'] = gpio - 1
        if xbus is not None:
            self._pnums['x'] = xbus - 1
        if name is not None:
            self._name = name
        else:
            self._name = 'mc{}'.format(Microcontroller._part_count)
        Microcontroller._part_count += 1
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
            ps[pnum] = pclass(self, name)
        return ps[pnum]

    def _normalize_port_name(self, name):
        """
        Takes a port name and returns its number and type.
        """
        pmap = {'p':GPIO, 'x':XBUS}
        ptype = name[0]
        pnum = name[1:]
        if ptype not in pmap:
            raise x.PortException("Unknown port type: "+ptype)
        if not pnum.isdigit():
            raise x.PortException("Invalid port number: "+pnum)
        pnum = int(pnum)
        if self._pnums[ptype] < pnum:
            raise x.PortException("Port out of supported range: "+name)
        return (pmap[ptype], pnum)

    def execute(self, code):
        lines = code.split('\n')
        for l in lines:
            self._run_line(l.strip())

    def _run_line(self, line):
        if line[0] == "#":
            return
        tokens = line.split(' ')
        command = tokens.pop(0)
        if command == "add":
            self._acc += int(tokens.pop(0))
        elif command == 'sub':
            self._acc -= int(tokens.pop(0))
        else:
            raise x.CommandException("Invalid command: "+command)

    @property
    def acc(self):
        return self._acc
    
    @property
    def name(self):
        return self._name


class Port():

    _parent = None  # Microcontroller
    _output = 0  # Output buffer.
    _circuit = None
    _name = ""

    def __init__(self, mc, name):
        self._parent = mc
        self._links = []
        self._name = name

    def write(self, val):
        self._output = val

    def read(self):
        """
        Returns the maximum output of all attached ports.
        """
        if self._circuit is None:
            return 0
        return self._circuit.max_value(self)

    def link(self, port):
        if not isinstance(port, Port):
            raise TypeError("Invalid port type: "+port.__class__.__name__)
        c = port._circuit
        if c is None:
            c = self._circuit or Circuit()
        c.link(self, port)
        self._circuit = c
        port._circuit = c

    def unlink(self):
        self._circuit.unlink(self)
        self._circuit = None

    @property
    def parent(self):
        return self._parent

    @property
    def output(self):
        return self._output

    @property
    def name(self):
        return self.parent.name+"."+self._name


class GPIO(Port):

    def write(self, val):
        """
        GPIO values are constant signals from 0 to 100.
        """
        val = int(val)
        if val > 100:
            val = 100
        if val < 0:
            val = 0
        self._output = val


class XBUS(Port):
    pass


class Circuit():

    _attached = None  # [Port, Port]

    def __init__(self):
        self._attached = []

    def link(self, *ports):
        for port in ports:
            if port in self._attached:
                continue
            self._validate_link(port)
            self._attached.append(port)

    def unlink(self, port):
        self._attached.remove(port)

    def max_value(self, exclude=None):
        out = []
        for p in self._attached:
            if p != exclude:
                out.append(p.output)
        if len(out) > 0:
            return max(out)
        return 0

    def _validate_link(self, port):
        for p in self._attached:
            if not isinstance(port, p.__class__):
                raise x.PortCompatException(
                    "Incompatible ports: {} / {}"
                    .format(self.__class__, port.__class__)
                )
            if p.parent == port.parent:
                raise x.PortSelfLinkException(
                    "Part linked to self ({} via {})"
                    .format(port.name, p.name)
            )
