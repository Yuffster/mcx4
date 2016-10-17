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

    _cpu = None  # CPU

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
        self._cpu = CPU(self)

    def __getattr__(self, name):
        reg = self.interface(name)
        if reg:
            return reg
        raise(AttributeError("Invalid attribute: {}".format(name)))

    def value(self, val):
        reg = self.interface(val)
        if reg:
            return reg.read()
        return int(val)

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
        self._registers = {}
        self._registers['acc'] = Register(self, 'acc')
        self._registers['null'] = NullRegister(self, 'null')
        for n in range(0, self._dats):
            name = "dat{}".format(n)
            self._registers[name] = Register(self, name)
        if self._dats > 0:
            # Handy alias when there's only one dat register.
            self._registers['dat'] = self._registers['dat0']

    def execute(self, code):
        self._cpu.execute(code)

    @property
    def name(self):
        return self._name

    @property
    def acc(self):
        acc = self.register('acc')
        return acc.read()


class Interface():

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
        if not isinstance(port, Interface):
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


class GPIO(Interface):

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


class XBUS(Interface):
    pass


class Circuit():

    _attached = None  # [Interface, Interface]

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
                    "Incompatible interfaces: {} / {}"
                    .format(self.__class__, port.__class__)
                )
            if p.parent == port.parent:
                raise x.PortSelfLinkException(
                    "Part linked to self ({} via {})"
                    .format(port.name, p.name)
            )


class Register():

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

class NullRegister(Register):

    """
    Supports read and write, but always returns 0.
    """

    def write(self, val):
        pass


class CPU():

    _insts = None  # []
    _mc = None  # Microcontroller
    _exec_plus = False  # Whether or not to execute +.
    _exec_minus = False  # Whether or not to execute -.
    _cursor = 0
    _labels = None  # {label:inst_num}

    def __init__(self, mc=None):
        self._mc = mc
        self.reset()

    def reset(self):
        self._insts = []
        self._exec_plus = False
        self._exec_minus = False
        self._cursor = 0
        self._labels = {}

    def execute(self, code):
        self.reset()
        if isinstance(code, tuple):
            self._insts = [code]
        elif isinstance(code, list):
            self._insts = code
        else:
            self.compile(code)
        while self._cursor < len(self._insts):
            c = self.exec_inst(self._insts[self._cursor])
            if c is not None:
                self._cursor = c
            else:
                self._cursor += 1
        self._cursor = 0

    def exec_inst(self, inst):
        """
        Executes one instruction.
        """
        command = inst[0]
        meth = getattr(self, 'do_'+command.lower(), None)
        if meth:
            return meth(*inst[1:])
        else:
            raise x.CommandException("Invalid instruction: "+command)

    def compile(self, code):
        """
        Compiles a string of code into a list of tuple instructions.

        Code looks like:

              teq p0 p1
            + mov p0 p1      ; This is a comment.
            - mov 100 p0     # This is a comment.
              add p0

        Compiled looks like:

            [
                ('test', 'eq', ('p0', 'p1')),
                ('cond', True, ('mov', 'p0', 'p1')),
                ('cond', False, ('mov', '100', 'p0')),
                ('add', 'p0')
            ]

        """
        out = []
        lines = code.split('\n')
        i = 0  # Instruction number (lines can be null and don't count)
        for l in lines:
            if ':' in l:  # Record and strip labels.
                label = l.split(':')
                self._labels[label[0].strip()] = i
                if len(label) == 2:
                    l = label[1]
                else:
                    l = ''
            l = l.split(';')[0]  # Strip comments and whitespace.
            l = l.split('#')[0]
            l = l.strip()
            if l == '':
                continue
            i += i  # Increment the instruction number.
            inst = tuple(l.split(' '))
            if inst[0] == '+':
                inst = ('cond', True, inst[1:])
            if inst[0] == '-':
                inst = ('cond', False, inst[1:])
            if inst[0][0] == 't':
                inst = ('test', inst[0][1:], inst[1:])
            out.append(inst)
        self._insts = out
        return out  # Only used for testing.

    def do_add(self, a):
        a = self._mc.value(a)
        self._mc.register('acc').write(self._mc.acc + a)

    def do_mul(self, a):
        a = self._mc.value(a)
        acc = self._mc.register('acc')
        acc.write(acc.read()*a)

    def do_sub(self, a):
        a = self._mc.value(a)
        self._mc.register('acc').write(self._mc.acc - a)

    def do_mov(self, a, b):
        a = self._mc.value(a)
        r2 = self._mc.interface(b)
        if r2 is None:
            raise x.RegisterException("Invalid register: "+b)
        r2.write(a)

    def do_not(self):
        acc = self._mc.register('acc')
        if acc.read() == 0:
            acc.write(100)
        else:
            acc.write(0)

    def do_jmp(self, label):
        if label not in self._labels:
            raise x.LabelException("Label not found: "+label)
        return self._labels[label]

    def do_test(self, comp, args):
        meth = getattr(self, 'test_'+comp, None)
        if meth is None:
            raise x.CommandException("Invalid comparison: "+comp)
        a = self._mc.value(args[0])
        b = self._mc.value(args[1])
        plus, minus = meth(a, b)  # Execute + or -.
        self._exec_plus = plus
        self._exec_minus = minus

    def do_cond(self, plus, inst):
        if plus and self._exec_plus:
            return self.exec_inst(inst)
        elif plus is False and self._exec_minus:
            return self.exec_inst(inst)

    def test_eq(self, a, b):
        return (a == b, a != b)

    def test_cp(self, a, b):
        return (a > b, a < b)

    def test_lt(self, a, b):
        return (a < b, not(a < b))

    def test_gt(self, a, b):
        return (a > b, not(a > b))
