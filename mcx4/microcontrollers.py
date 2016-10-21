import mcx4.exceptions as x
from mcx4.cpus import CPU
from mcx4.interfaces import GPIO, XBUS, Register, NullRegister, Interface
from mcx4 import time


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

    _sleep_until = 0  # Keeps track of sleep state.

    _board = None  # Board

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

    def set_board(self, board):
        """
        The board object represents the global context, and will
        effect whether or not port I/O is instantaneous or based
        on nonparallel cycles.
        """
        self._board = board

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
        """
        Compile and immediately execute code in one go.
        """
        self._cpu.execute(code)

    def compile(self, code):
        """
        Load code into the CPU.

        Replaces existing code.
        """
        self._cpu.compile(code)

    def step(self):
        """
        Execute the next instruction.
        """
        if self.sleeping() is False:
            self._cpu.step()

    def sleep(self, atus):
        self._sleep_until = time.end_time(atus)

    def sleeping(self):
        if time.get() is None or self._sleep_until is 0:
            return False
        if time.get() >= self._sleep_until:
            self._sleep_until = 0
            return False
        return self._sleep_until

    @property
    def name(self):
        return self._name

    @property
    def acc(self):
        acc = self.register('acc')
        return acc.read()


class MC4000(Microcontroller):

    _gpios = 2
    _xbuses = 1
    _dats = 0

class MC4000X(Microcontroller):

    _gpios = 0
    _xbuses = 4
    _dats = 0

class MC6000(Microcontroller):

    _gpios = 2
    _xbuses = 4
    _dats = 1
