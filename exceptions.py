class PortException(Exception): pass
class PortSelfLinkException(PortException): pass
class PortCompatException(PortException): pass
class RegisterException(PortException): pass
class RunException(Exception): pass
class LabelException(RunException): pass
class CommandException(RunException): pass