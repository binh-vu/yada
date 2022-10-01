from yada.argname import ArgumentName


class NotSupportedType(Exception):
    def __init__(self, argname: ArgumentName, argtype: type, msg: str = ""):
        super().__init__(
            f"Type {argtype} of field {'.'.join(argname.names)} is not supported{msg if len(msg) == 0 else ': ' + msg}"
        )
