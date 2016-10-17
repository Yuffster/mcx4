import exceptions as x

class Microcontroller():

    _gpios = 0
    _xbuses = 0
    _dats = 0
    
    _registers = None  # {name:Interface}

    _pnums = None  # {type:number}
    _ports = None  # {name:[Port,Port...]}

    _name = ""

    _part_count = 0  # static

    def __init__(self, name=None, gpio=None, xbus=None, dats=None):
        self._pnums = {'p':self._gpios, 'x':self._xbuses}
        if gpio is not None:
            self._pnums['p'] = gpio - 1
        if xbus is not None:
            self._pnums['x'] = xbus - 1
        if name is not None:
            self._name = name
        if dats is not None:
            self._dats = dats
        else:
            self._name = 'mc{}'.format(Microcontroller._part_count)
        Microcontroller._part_count += 1
        self._initialize_registers()
        self._ports = {'p':{}, 'x':{}}

    def __getattr__(self, name):
        reg = self.interface(name)
        if reg:
            return reg
        raise(AttributeError("Invalid attribute: {}".format(name)))

    def interface(self, name):
        name = name.lower()
        try:
            reg = self.register(name)
        except x.RegisterException:
            reg = False
        if reg is not False:
            return reg
        # Check ports if it's a valid port name.
        if name[0].isalpha() and name[1:].isdigit():
            return self.get_port(name)
        return None

    def get_port(self, name):
        name = name.lower()
        pclass, pnum = self._normalize_port_name(name)
        ps = self._ports[name[0]]
        if pnum not in ps:
            ps[pnum] = pclass(self, name)
        return ps[pnum]

    def register(self, name):
        """
        Returns either an Interface with read() and write().
        """
        name = name.lower()
        if name in self._registers:
            return self._registers[name]
        raise x.RegisterException("Register not found: "+name)

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

    def _initialize_registers(self):
        self._registers = {'acc': Interface(self, 'acc')}
        for n in range(0, self._dats):
            name = "dat{}".format(n)
            self._registers[name] = Interface(self, name)
        if self._dats > 0:
            # Handy alias when there's only one dat register.
            self._registers['dat'] = self._registers['dat0']

    def execute(self, code):
        lines = code.split('\n')
        for l in lines:
            self._run_line(l.strip())

    def _run_line(self, line):
        CPU.execute(self, line)

    @property
    def name(self):
        return self._name

    @property
    def acc(self):
        acc = self.register('acc')
        return acc.read()


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


class Interface():

    _val = 0
    _name = ''
    _parent = None  # Microcontroller, probably.

    def __init__(self, parent, name=''):
        self._name = name
        self._parent = parent

    def read(self):
        return self._val

    def write(self, val):
        self._val = int(val)

    def inc(self, n=1):
        self._val += 1

    def dec(self, n=1):
        self._val -= n


class CPU():

    def execute(self, mc, line):
        if line[0] == "#":
            return
        words = line.split(' ')
        command = words.pop(0)
        meth = getattr(self, 'do_'+command, None)
        if meth:
            return meth(mc, *words)
        raise x.CommandException("Invalid instruction: "+command)

    def do_add(self, mc, a):
        r1 = mc.interface(a)
        if r1 is not None:
            a = r1.read()
        a = int(a)
        mc.register('acc').write(mc.acc + a)

    def do_sub(self, mc, a):
        r1 = mc.interface(a)
        if r1 is not None:
            a = r1.read()
        a = int(a)
        mc.register('acc').write(mc.acc - a)


CPU = CPU()  # Singleton is the only design pattern I know.
