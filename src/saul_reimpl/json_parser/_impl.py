from __future__ import annotations
from typing import Any, Never
import json

type JsonPrimative = list[JsonPrimative] | JsonObject | int | str | float | bool | None
type JsonObject = dict[str, JsonPrimative] | list[JsonPrimative]


def error() -> Never:
    raise RuntimeError("")


class JsonParser:
    _pointer: int = 0
    _string: str

    def _char(self) -> str:
        return self._string[self._pointer]

    def _read_spaces(self) -> None:
        while self._char() == " ":
            self._pointer += 1

    def _assert_char_and_advance(self, char: str) -> None:
        if self._char() != char:
            error()
        self._pointer += 1

    def _process_string(self) -> str:
        self._assert_char_and_advance('"')

        string = ""
        while (char := self._char()) != '"':
            string += char
            self._pointer += 1
        self._pointer += 1
        return string

    def _process_bool_or_null(self) -> bool | None:
        word = ""
        while (char := self._char()).isalpha():
            word += char
            self._pointer += 1

        return {"true": True, "false": False, "null": None}[word]

    def _process_int_or_float(self) -> int | float:
        number = ""
        while (digit := self._char()) in "-1234567890.":
            number += digit
            self._pointer += 1

        return float(number) if "." in number else int(number)

    def _process_primative(self) -> JsonPrimative:
        if self._char() in "-1234567890":
            return self._process_int_or_float()
        elif self._char() == '"':
            return self._process_string()
        elif self._char() == "{":
            return self._process_dict()
        elif self._char() == "[":
            return self._process_list()
        else:
            return self._process_bool_or_null()

    def _process_dict(self) -> dict[str, JsonPrimative]:
        self._assert_char_and_advance("{")
        self._read_spaces()

        OBJ: dict[str, JsonPrimative] = {}
        while True:
            if self._char() == "}":
                self._pointer += 1
                break

            self._read_spaces()

            key = self._process_string()
            self._read_spaces()
            self._assert_char_and_advance(":")
            self._read_spaces()

            OBJ[key] = self._process_primative()

            self._read_spaces()
            if self._char() == "}":
                self._pointer += 1
                break

            self._read_spaces()
            self._assert_char_and_advance(",")
            self._read_spaces()

        return OBJ

    def _process_list(self) -> list[JsonPrimative]:
        self._assert_char_and_advance("[")
        self._read_spaces()

        l: list[JsonPrimative] = []
        while True:
            if self._char() == "]":
                self._pointer += 1
                break
            self._read_spaces()

            l.append(self._process_primative())
            self._read_spaces()
            if self._char() == "]":
                self._pointer += 1
                break

            self._read_spaces()
            self._assert_char_and_advance(",")
            self._read_spaces()

        return l

    def parse(self, string: str) -> JsonObject:
        self._pointer: int = 0
        self._string = string
        self._read_spaces()

        ret: JsonObject
        if self._char() == "{":
            ret = self._process_dict()
        elif self._char() == "[":
            ret = self._process_list()
        else:
            error()

        try:
            self._read_spaces()
        except IndexError:
            return ret

        error()


# def text_to_json(string: str) -> dict[Any, Any]:
#     obj = {}
#     return obj


# a = JsonParser()
# print(a.parse('{"test": 123, "hello": [1,2,3,4]}'))
a = JsonParser()


def check(s: str) -> None:
    assert a.parse(s) == json.loads(s), f"Mismatch for: {s}"


# ------------------
# Basic
# ------------------
check("{} ")
check('{"a":1}')
check('{"a":1,"b":2}')

# ------------------
# Whitespace variations
# ------------------
check('{ "a" : 1 }')
check('  {"a":1,"b":2}   ')
check('{"a":1 , "b" :2}')

# ------------------
# Arrays
# ------------------
check("[1,2,3]")
check("[ 1 , 2 , 3 ]")
check('{"arr":[1,2,3]}')

# ------------------
# Nested structures
# ------------------
check('{"a":{"b":{"c":3}}}')
check('{"x":[1,{"y":[2,3]},4]}')
check('{"a":[{"b":1},{"c":2}]}')

# ------------------
# Numbers
# ------------------
check('{"i":0}')
check('{"neg":-5}')
check('{"big":123456789}')
check('{"float":3.14}')

# ------------------
# Empty structures
# ------------------
check("[]")
check("[[]]")
check("[{}]")
check('{"a":{}}')
check('{"a":[]}')

# ------------------
# Mixed realistic
# ------------------
check('{"users":[{"id":1,"name":"a"},{"id":2,"name":"b"}]}')

# ------------------
# Deeper nesting
# ------------------
check('{"a":[1,{"b":[2,{"c":[3,4,{"d":5}]}]}]}')

# ------------------
# Large object
# ------------------
big_obj = "{" + ",".join([f'"k{i}":{i}' for i in range(50)]) + "}"
check(big_obj)

# ------------------
# Large array
# ------------------
big_arr = "[" + ",".join(str(i) for i in range(200)) + "]"
check(big_arr)

# ------------------
# Combined large structure
# ------------------
combo = '{"data":' + big_obj + ',"arr":' + big_arr + "}"
check(combo)

print("All tests passed!")
