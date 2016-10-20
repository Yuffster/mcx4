import mcx4.exceptions as x

class CPU():

    _insts = None  # []
    _mc = None  # Microcontroller
    _exec_plus = False  # Whether or not to execute +.
    _exec_minus = False  # Whether or not to execute -.
    _inst_pointer = 0  # Instruction pointer.
    _labels = None  # {label:inst_num}

    def __init__(self, mc=None):
        self._mc = mc
        self.reset()

    def reset(self):
        self._insts = []
        self._exec_plus = False
        self._exec_minus = False
        self._inst_pointer = 0
        self._labels = {}

    def execute(self, code):
        """
        Runs through the code once without looping.

        Resets all the state stuff before it starts.
        """
        self.reset()
        if isinstance(code, tuple):
            self._insts = [code]
        elif isinstance(code, list):
            self._insts = code
        else:
            self.compile(code)
        while self._inst_pointer < len(self._insts):
            self.step(loop=False)
        self._inst_pointer = 0

    def step(self, loop=True):
        """
        Execute the next instruction.

        If a cursor is returned, e.g. after a jump, the cursor will be
        updated to that value.  Otherwise, the cursor will be incremented.

        Cursor will be reset to 0 after all instructions are complete,
        so stepping will loop the execution, unless loop is set to False.
        """
        c = self.exec_inst(self._insts[self._inst_pointer])
        if c is not None:
            self._inst_pointer = c
        else:
            self._inst_pointer += 1
        # Start over if we're done.
        if loop and self._inst_pointer == len(self._insts):
            self._inst_pointer = 0

    def exec_inst(self, inst):
        """
        Executes a given compiled instruction.

        Returns the new cursor in case of a jump.
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

        Replaces any current instruction set with this one.

        Doesn't reset registers.

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

    def do_sub(self, a):
        a = self._mc.value(a)
        self._mc.register('acc').write(self._mc.acc - a)

    def do_mul(self, a):
        a = self._mc.value(a)
        acc = self._mc.register('acc')
        acc.write(acc.read()*a)

    def do_not(self):
        acc = self._mc.register('acc')
        if acc.read() == 0:
            acc.write(100)
        else:
            acc.write(0)

    def do_dgt(self, bit):
        """
        Rewrite ACC with one isolated digit.

        Decimal little-endian.
        """
        bit = self._mc.value(bit)
        acc = self._mc.register('acc')
        val = str(acc.read())[::-1]
        if len(val) > bit:
            acc.write(val[bit])
        else:
            acc.write(0)

    def do_dst(self, bit, val):
        """
        Set ACC digit to the least significant digit of the provided
        value.  Decimal little-endian.
        """
        bit = self._mc.value(bit)
        bit = int(str(bit)[-1])  # Least significant digit.
        val = self._mc.value(val)
        val = str(val)[-1]  # Least significant digit.
        acc = self._mc.register('acc')
        new = list(str(acc.read())[::-1])
        if len(new) > bit:
            new[bit] = val
            new = str(''.join(new[::-1]))
        else:
            new = 0
        acc.write(new)

    def do_mov(self, a, b):
        a = self._mc.value(a)
        r2 = self._mc.interface(b)
        if r2 is None:
            raise x.RegisterException("Invalid register: "+b)
        r2.write(a)

    def do_jmp(self, label):
        if label not in self._labels:
            raise x.LabelException("Label not found: "+label)
        return self._labels[label]

    def do_nop(self):
        pass  # Easiest instruction ever.

    def do_slp(self, a):
        a = self._mc.value(a)
        self._mc.sleep(a)

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
