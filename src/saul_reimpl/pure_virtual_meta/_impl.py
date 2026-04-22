from abc import ABCMeta, abstractmethod

from contextlib import contextmanager


@contextmanager
def throws_exception(exception: Exception):
    _raised_exception = False
    try:
        yield
    except exception:
        _raised_exception = True
    assert _raised_exception, f"Did not raise exception {exception}"


class CustomMeta(ABCMeta):
    def __new__(cls, name, bases, dct):
        # Only apply when directly inheriting from AbstractClass
        direct_from_root = any(base.__name__ == "AbstractClass" for base in bases)

        if direct_from_root:
            for key, value in dct.items():
                if callable(value) and not key.startswith("__"):
                    dct[key] = abstractmethod(value)

        return super().__new__(cls, name, bases, dct)


class AbstractClass(metaclass=CustomMeta): ...


class A(AbstractClass):
    def a(self): ...


class B(A):
    def a(self):
        return "B"


class C(A): ...


b = B()
assert "B" == b.a()

with throws_exception(TypeError):
    c = C()
