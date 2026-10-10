"""MicroPython helpers used as decorators and compile-time consts."""


def const(x):
    return x


def native(fn=None):
    if fn is None:
        return lambda wrapped: wrapped
    return fn


def viper(fn=None):
    if fn is None:
        return lambda wrapped: wrapped
    return fn


def mem_info(verbose=False):
    return None
