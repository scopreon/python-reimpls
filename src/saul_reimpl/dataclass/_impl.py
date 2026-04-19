from typing import TypeVar

T = TypeVar("T")


def _hash(self):
    return hash(
        tuple(getattr(self, name) for name in type(self).__annotations__.keys())
    )


def _eq(self, obj2):
    return all(
        getattr(self, name) == getattr(obj2, name)
        for name in self.__annotations__.keys()
    )


def _repr(self) -> str:
    attrs = (f"{name}={getattr(self, name)}" for name in type(self).__annotations__)
    return f"{type(self).__name__}<{', '.join(attrs)}>"


def dataclass(_cls=None, *, hash=False, eq=False, repr=False):
    def wrap(cls):
        if hash and not eq:
            raise Exception("Must have hash and eq")
        if eq:
            setattr(
                cls,
                "__eq__",
                _eq,
            )
        if hash:
            setattr(cls, "__hash__", _hash)
        else:
            setattr(cls, "__hash__", None)
        if repr:
            setattr(cls, "__repr__", _repr)

        return cls

    if _cls is None:
        return wrap
    return wrap(_cls)


@dataclass(repr=True, hash=True, eq=True)
class A:
    integer: int
    string: str


a = A()
a.string = "jwiojfw"
a.integer = 123

print(a)
s = set({a})
