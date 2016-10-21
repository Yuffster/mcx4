from mcx4 import time
from mcx4.microcontrollers import Microcontroller

class Board():

    _items = None  # List of items to step.
    _sleep_until = None

    def __init__(self):
        if time.get() is None:
            time.advance_cycle()
        self._items = []

    def add(self, thing):
        if not isinstance(thing, Microcontroller):
            raise TypeError("Object added to board must be Microcontroller.")
        if thing not in self._items:
            self._items.append(thing)
        thing.set_board(self)

    def step(self):
        """
        Step one cycle.
        """
        if len(self._items) == 0:
            return
        sleeps = []
        for i in self._items:
            sleep = i.sleeping()
            if sleep is False:
                i.step()
            else:
                sleeps.append(sleep)
        if len(sleeps) == len(self._items):
            # Awww, everyone's sleeping.
            # Advance time to the next wake.
            time.set(min(sleeps))
        time.advance_cycle()

    def advance(self):
        """
        Step for one arbitrary time unit.
        """
        end = time.end_time(1)
        while time.get() < end:
            self.step()
