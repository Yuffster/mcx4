_cycles = None
_cycles_per_ATU = 1000  # Cycles per arbitrary time unit.


def get():
    """
    Returns the current time in arbitrary time units.
    """
    global _cycles
    return _cycles


def set(time):
    global _cycles
    _cycles = time


def advance_cycle():
    """
    Advance time by one cycle.
    """
    global _cycles
    if _cycles is None:  # Let other modules know we're tracking time.
        _cycles = 0
    _cycles += 1


def end_time(atus):
    """ Returns the number of cycles after the end of the ATU. """
    global _cycles_per_ATU
    return get() + atus * _cycles_per_ATU
