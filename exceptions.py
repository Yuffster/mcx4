class PortException(Exception): pass
class PortSelfLinkException(PortException): pass
class PortCompatException(PortException): pass
class CommandException(PortException): pass
class RegisterException(PortException): pass