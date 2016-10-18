import mcx4.exceptions as x

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
